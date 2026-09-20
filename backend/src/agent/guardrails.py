"""Pre-LLM and Post-LLM safety guardrails."""

import re
from typing import Any

from services.rules_engine import detect_legal_threat


def check_pre_llm_legal_threat(content: str) -> bool:
    """Pre-LLM Guardrail: Detects legal/formal complaint threats before invoking LLM.

    Emotional expression ('I'm furious') alone will NOT trigger detection.
    If True, LLM execution is bypassed and mandatory legal escalation occurs.
    """
    return detect_legal_threat(content)


PROHIBITED_PATTERNS = [
    r"\bsk-999\b",
    r"\bbusiness-class upgrade confirmed\b",
    r"\bfree business-class upgrade\b",
    r"\bfree business class upgrade\b",
    r"\bwaived the (?:rs\.?\s*)?2,?000\b",
    r"\bwaived the fare difference\b",
    r"\bfree higher-fare flight\b",
    r"\bfull-night hotel\b",
    r"\bhotel for the whole night\b",
]

COMPILED_PROHIBITED_REGEX = re.compile("|".join(PROHIBITED_PATTERNS), re.IGNORECASE)


def validate_post_llm(reply_text: str, allowed_facts: dict[str, Any] | None = None) -> bool:
    """Post-LLM Guardrail: Validates LLM response draft against policy violations & hallucinations.

    Returns True if response is safe and compliant; False if response contains prohibited fabrications.
    """
    if not reply_text:
        return False

    # 1. Check prohibited patterns
    if COMPILED_PROHIBITED_REGEX.search(reply_text):
        return False

    # 2. Check fabricated flight numbers if allowed flight numbers are supplied
    if allowed_facts and "allowed_flight_numbers" in allowed_facts:
        allowed_flights = allowed_facts["allowed_flight_numbers"]
        # Match flight pattern SK-XXX
        mentioned_flights = re.findall(r"\bSK-\d{3,4}\b", reply_text, re.IGNORECASE)
        for flight in mentioned_flights:
            if flight.upper() not in [f.upper() for f in allowed_flights if f]:
                return False

    return True
