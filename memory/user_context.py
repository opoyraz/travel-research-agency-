"""
Travel Research Agency — User Context Memory (S6)
Reads/writes user preferences using LangGraph Store (long-term memory).
Store persists across threads — user preferences carry over between conversations.

Two nodes:
  - load_user_context: runs at START, injects preferences into messages
  - save_preferences: runs at END, extracts and stores new preferences
"""

import uuid
from langchain_core.messages import SystemMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from langgraph.store.base import BaseStore


# ═══════════════════════════════════════════════
#  LOAD: Read long-term memory → inject into conversation
# ═══════════════════════════════════════════════

def load_user_context(state: dict, **kwargs) -> dict:
    return {}



# ═══════════════════════════════════════════════
#  SAVE: Extract preferences from conversation → write to store
# ═══════════════════════════════════════════════

def save_preferences(state: dict, **kwargs) -> dict:
    return {}

# ═══════════════════════════════════════════════
#  SAVE TRIP: Store completed trip for future personalization
# ═══════════════════════════════════════════════

def save_trip(state: dict, config: RunnableConfig, *, store: BaseStore) -> dict:
    """Save a completed trip to long-term memory."""
    user_id = config["configurable"].get("user_id", "anonymous")
    namespace = (user_id, "past_trips")
    trip_id = str(uuid.uuid4())[:8]

    store.put(namespace, f"trip-{trip_id}", {
        "destination": state.get("destination", "Unknown"),
        "dates": state.get("travel_dates", "Unknown"),
        "budget_spent": state.get("estimated_total", 0),
        "status": state.get("status", "completed"),
    })

    return {}
