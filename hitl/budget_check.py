"""
Travel Research Agency — Budget Check
Auto-approves with warning (HITL disabled without checkpointer).
"""

from langchain_core.messages import AIMessage


def budget_check_node(state: dict) -> dict:
    estimated = state.get("estimated_total", 0)
    budget = state.get("budget", 5000)

    if estimated > budget:
        return {"messages": [AIMessage(
            content=f"⚠️ Estimated ${estimated:,.0f} exceeds ${budget:,.0f} budget. Proceeding anyway."
        )]}

    return {}