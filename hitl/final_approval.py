
from langchain_core.messages import AIMessage


def final_approval_node(state: dict) -> dict:
    """Final approval — auto-approves (HITL disabled without checkpointer)."""
    from langchain_core.messages import AIMessage
    return {"messages": [AIMessage(content="✅ Itinerary approved.")], "status": "booked"}