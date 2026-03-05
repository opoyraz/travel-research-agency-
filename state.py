"""
Travel Research Agency — Shared State Definition
Combines fields from all sections: S2 (core), S3 (tools), S4 (RAG),
S5 (guardrails), S6 (memory), S7 (HITL), S8 (full graph).
"""

from typing import Annotated, Optional
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages


class TravelState(TypedDict):
    # ── Core (S2) ──
    messages: Annotated[list, add_messages]
    destination: Optional[str]
    travel_dates: Optional[str]
    num_travelers: Optional[int]

    # ── Budget (S2/S3) ──
    budget: Optional[float]
    estimated_total: Optional[float]
    cost_breakdown: Optional[dict]

    # ── Safety (S4) ──
    advisory_level: Optional[int]
    rag_context: Optional[str]

    # ── Guardrails (S5) ──
    guardrail_status: Optional[str]       # "pass" | "block"
    injection_status: Optional[str]       # "safe" | "blocked"
    factuality_status: Optional[str]      # "pass" | "retry"
    output_status: Optional[str]          # "pass" | "retry"
    retry_count: Optional[int]

    # ── Workflow control (S7) ──
    status: Optional[str]                 # "active" | "booked" | "cancelled"
    replan_requested: Optional[bool]
    booking_confirmed: Optional[bool]
