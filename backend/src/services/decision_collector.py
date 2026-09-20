"""Turn-based collector for deterministic rules_engine decision traces."""

import contextvars
from typing import Any
from pydantic import BaseModel


class DecisionTraceItem(BaseModel):
    rule: str
    inputs: dict[str, Any]
    outcome: Any
    reason_code: str | None = None


_decision_trace_ctx: contextvars.ContextVar[list[DecisionTraceItem]] = contextvars.ContextVar(
    "_decision_trace_ctx"
)


def reset_decision_trace() -> None:
    """Resets/initializes the decision trace collector for the current turn."""
    _decision_trace_ctx.set([])


def get_decision_trace() -> list[DecisionTraceItem]:
    """Retrieves all collected decision trace items for the current turn."""
    return list(_decision_trace_ctx.get([]))


def record_decision_trace(
    rule: str,
    inputs: dict[str, Any],
    outcome: Any,
    reason_code: str | None = None,
) -> None:
    """Appends a deterministic decision trace item to the current turn's collector."""
    try:
        current_list = _decision_trace_ctx.get()
    except LookupError:
        current_list = []
        _decision_trace_ctx.set(current_list)

    # Avoid exact duplicate adjacent entries in the same turn
    for item in current_list:
        if (
            item.rule == rule
            and item.inputs == inputs
            and item.reason_code == reason_code
        ):
            return

    trace_item = DecisionTraceItem(
        rule=rule,
        inputs=inputs,
        outcome=outcome,
        reason_code=reason_code,
    )
    current_list.append(trace_item)
    _decision_trace_ctx.set(current_list)
