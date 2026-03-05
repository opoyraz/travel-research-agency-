"""
Travel Research Agency — Routing Functions
All conditional edge functions for the LangGraph graph.
Maps to: S5 (guardrails), S7 (HITL), S8 (full graph).
"""


# ══════════════════════════════════════════
#  GUARDRAIL ROUTING (S5)
# ══════════════════════════════════════════

def route_after_input_guard(state: dict) -> str:
    """Pass → injection guard, Block → end."""
    if state.get("guardrail_status") == "pass":
        return "injection_guard"
    return "__end__"


def route_after_injection(state: dict) -> str:
    """Safe → supervisor, Blocked → end."""
    if state.get("injection_status") == "safe":
        return "supervisor"
    return "__end__"


def route_after_factuality(state: dict) -> str:
    """Pass → back to supervisor, Retry → re-run safety (max 2)."""
    if state.get("factuality_status") == "retry" and (state.get("retry_count", 0) < 2):
        return "safety_analyst"
    return "supervisor"


# ══════════════════════════════════════════
#  HITL ROUTING (S7)
# ══════════════════════════════════════════

def route_after_budget_check(state: dict) -> str:
    """Approve → writer, Replan → budget_optimizer, Cancel → end."""
    if state.get("status") == "cancelled":
        return "__end__"
    if state.get("replan_requested"):
        return "budget_optimizer"
    return "writer"


def route_after_final_approval(state: dict) -> str:
    """Approve → output guard, Edit → writer, Cancel → end."""
    if state.get("status") == "cancelled":
        return "__end__"
    if state.get("replan_requested"):
        return "writer"
    return "output_guard"


# ══════════════════════════════════════════
#  OUTPUT ROUTING
# ══════════════════════════════════════════

def route_after_output_guard(state: dict) -> str:
    """Pass → save prefs, Retry → writer."""
    if state.get("output_status") == "retry":
        return "writer"
    return "save_preferences"
