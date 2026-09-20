"""Real LangChain Tool-Calling Agent implementation with safety guardrails."""

import datetime
import logging
from typing import Any
from sqlalchemy.orm import Session

import langchain
if not hasattr(langchain, "verbose"):
    langchain.verbose = False
if not hasattr(langchain, "debug"):
    langchain.debug = False
if not hasattr(langchain, "llm_cache"):
    langchain.llm_cache = None

from agent.fallback import generate_fallback_response
from agent.guardrails import check_pre_llm_legal_threat, validate_post_llm
from agent.prompts import SYSTEM_PROMPT
from agent.stub import AgentInterface
from agent.tools import AGENT_TOOLS
from core.config import settings
from models.conversation import Conversation
from models.message import Message
import repositories.action_repo as action_repo
import repositories.booking_repo as booking_repo
import repositories.conversation_repo as conversation_repo
import repositories.customer_repo as customer_repo
import repositories.escalation_repo as escalation_repo
from services.decision_collector import get_decision_trace, reset_decision_trace
import services.escalation_service as escalation_service
from schemas.chat import MessageResponse

logger = logging.getLogger("airline_resolution")


class RealAgent(AgentInterface):
    """LangChain Tool-Calling Agent for airline disruption resolution."""

    def respond(
        self, db: Session, conversation_id: int, content: str
    ) -> MessageResponse:
        """Processes customer chat message, enforces safety guardrails, and returns resolution response."""
        reset_decision_trace()

        conversation = conversation_repo.get_by_id(db, conversation_id)
        if not conversation:
            return MessageResponse(
                reply="Conversation record not found.",
                actions_taken=[],
                escalation=True,
                conversation_id=conversation_id,
                decision_trace=get_decision_trace(),
            )

        customer_id = conversation.customer_id

        # 1. PRE-LLM GUARDRAIL — Legal / Formal Complaint Threat Check
        if check_pre_llm_legal_threat(content):
            logger.info("Pre-LLM guardrail triggered legal threat detection. Bypassing LLM.")
            # Save user message
            user_msg = Message(
                conversation_id=conversation_id,
                role="user",
                content=content,
                created_at=datetime.datetime.utcnow(),
            )
            db.add(user_msg)

            # Create mandatory escalation
            escalation_service.create_escalation(
                db,
                reason_code="LEGAL_OR_FORMAL_COMPLAINT",
                summary=f"Legal threat or formal complaint detected: '{content}'",
                customer_id=customer_id,
                conversation_id=conversation_id,
            )

            escalation_reply = (
                "I'm escalating this to our specialist support team right now, "
                "and they'll reach out to you directly."
            )
            assistant_msg = Message(
                conversation_id=conversation_id,
                role="assistant",
                content=escalation_reply,
                created_at=datetime.datetime.utcnow(),
            )
            db.add(assistant_msg)
            db.commit()

            return MessageResponse(
                reply=escalation_reply,
                actions_taken=[],
                escalation=True,
                conversation_id=conversation_id,
                decision_trace=get_decision_trace(),
            )

        # 2. CHECK LLM API KEY CONFIGURATION
        if not settings.has_llm_key():
            logger.info("LLM_API_KEY is not configured. Invoking deterministic fallback engine.")
            fallback_res = generate_fallback_response(db, customer_id, conversation_id, content)

            user_msg = Message(
                conversation_id=conversation_id,
                role="user",
                content=content,
                created_at=datetime.datetime.utcnow(),
            )
            assistant_msg = Message(
                conversation_id=conversation_id,
                role="assistant",
                content=fallback_res["reply"],
                created_at=datetime.datetime.utcnow(),
            )
            db.add(user_msg)
            db.add(assistant_msg)
            db.commit()

            return MessageResponse(
                reply=fallback_res["reply"],
                actions_taken=fallback_res["actions_taken"],
                escalation=fallback_res["escalation"],
                conversation_id=conversation_id,
                decision_trace=get_decision_trace(),
            )

        # 3. RUN LANGCHAIN TOOL-CALLING AGENT WITH TIMEOUT & RETRIES
        try:
            from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
            from langgraph.prebuilt import create_react_agent

            provider = settings.LLM_PROVIDER.lower().strip() if settings.LLM_PROVIDER else "openai"
            if provider == "gemini":
                from langchain_google_genai import ChatGoogleGenerativeAI
                llm = ChatGoogleGenerativeAI(
                    model=settings.LLM_MODEL or "gemini-1.5-flash",
                    google_api_key=settings.LLM_API_KEY,
                    request_timeout=settings.LLM_TIMEOUT_SECONDS,
                    max_retries=settings.LLM_MAX_RETRIES,
                )
            elif provider == "groq":
                from langchain_groq import ChatGroq
                llm = ChatGroq(
                    model=settings.LLM_MODEL or "llama-3.3-70b-versatile",
                    groq_api_key=settings.LLM_API_KEY,
                    timeout=settings.LLM_TIMEOUT_SECONDS,
                    max_retries=settings.LLM_MAX_RETRIES,
                )
            else:
                from langchain_openai import ChatOpenAI
                llm = ChatOpenAI(
                    model=settings.LLM_MODEL or "gpt-4o-mini",
                    api_key=settings.LLM_API_KEY,
                    request_timeout=settings.LLM_TIMEOUT_SECONDS,
                    max_retries=settings.LLM_MAX_RETRIES,
                )

            # create_react_agent runs the full tool-calling loop (ReAct):
            # LLM → tool call → tool result → LLM → ... → final text reply.
            agent_executor = create_react_agent(llm, AGENT_TOOLS, state_modifier=SYSTEM_PROMPT)

            customer_obj = customer_repo.get_by_id(db, customer_id)
            customer_bookings = booking_repo.list_by_customer(db, customer_id)
            b_lines = [
                f"PNR: {b.pnr}, Segment: {b.segment_label}, Flight: {b.flight_no or 'N/A'}, Route: {b.route}, Status: {b.status}, Delay: {b.delay_minutes or 0}m"
                for b in customer_bookings
            ]
            b_str = "; ".join(b_lines) if b_lines else "None"

            input_messages = [
                HumanMessage(
                    content=(
                        f"Authenticated Customer: ID {customer_id}, Name: {customer_obj.name if customer_obj else 'Customer'}, Tier: {customer_obj.tier if customer_obj else 'Standard'}\n"
                        f"Customer Active Bookings: {b_str}\n"
                        f"Message: {content}"
                    )
                ),
            ]

            result = agent_executor.invoke({"messages": input_messages})

            # Extract the final AI text reply from the message history
            raw_reply = ""
            for msg in reversed(result.get("messages", [])):
                if isinstance(msg, AIMessage) and msg.content:
                    raw_reply = str(msg.content)
                    break

            # Allowed facts dictionary for post-LLM validation
            allowed_facts = {
                "allowed_flight_numbers": ["SK-204", "SK-118", "SK-305"],
                "customer_id": customer_id,
            }

            # 4. POST-LLM GUARDRAIL — Validate response draft against hallucinations & illegal waivers
            if not validate_post_llm(raw_reply, allowed_facts):
                logger.warning("Post-LLM guardrail validation failed for LLM draft. Reverting to fallback.")
                fallback_res = generate_fallback_response(db, customer_id, conversation_id, content)
                final_reply = fallback_res["reply"]
                actions_taken = fallback_res["actions_taken"]
                is_escalated = fallback_res["escalation"]
            else:
                final_reply = raw_reply
                db_actions = action_repo.list_by_conversation(db, conversation_id)
                actions_taken = [{"action_type": a.action_type, "details": a.details_json} for a in db_actions]
                db_escalations = escalation_repo.list_by_conversation(db, conversation_id)
                is_escalated = len(db_escalations) > 0

            user_msg = Message(
                conversation_id=conversation_id,
                role="user",
                content=content,
                created_at=datetime.datetime.utcnow(),
            )
            assistant_msg = Message(
                conversation_id=conversation_id,
                role="assistant",
                content=final_reply,
                created_at=datetime.datetime.utcnow(),
            )
            db.add(user_msg)
            db.add(assistant_msg)
            db.commit()

            return MessageResponse(
                reply=final_reply,
                actions_taken=actions_taken,
                escalation=is_escalated,
                conversation_id=conversation_id,
                decision_trace=get_decision_trace(),
            )

        except Exception as exc:
            logger.error("LangChain agent execution error: %s. Falling back to deterministic engine.", exc)
            fallback_res = generate_fallback_response(db, customer_id, conversation_id, content)

            user_msg = Message(
                conversation_id=conversation_id,
                role="user",
                content=content,
                created_at=datetime.datetime.utcnow(),
            )
            assistant_msg = Message(
                conversation_id=conversation_id,
                role="assistant",
                content=fallback_res["reply"],
                created_at=datetime.datetime.utcnow(),
            )
            db.add(user_msg)
            db.add(assistant_msg)
            db.commit()

            return MessageResponse(
                reply=fallback_res["reply"],
                actions_taken=fallback_res["actions_taken"],
                escalation=fallback_res["escalation"],
                conversation_id=conversation_id,
                decision_trace=get_decision_trace(),
            )


real_agent = RealAgent()
