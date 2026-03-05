"""
Travel Research Agency — Experience Planner Agent
Finds restaurants, tours, and activities at the destination.
Uses Gemini 2.0 Flash + MCP tools (search_restaurants, search_activities).
"""

from langchain_core.messages import SystemMessage, HumanMessage
from config import AGENT_MODELS


EXPERIENCE_PROMPT = """You are the Experience Planner. Find restaurants, tours,
and activities at the travel destination. Use the search_restaurants and
search_activities tools.

Format your findings as:
🍽️ RESTAURANTS:
- [Name] — [Cuisine] — $[Price Range] ([Rating])

🎯 ACTIVITIES:
- [Activity] — $[Cost] ([Duration], [Category])

Prioritize highly-rated options. Include a mix of price ranges.
Consider the traveler's budget when making recommendations."""


def experience_node(state: dict) -> dict:
    """Experience Planner agent: finds restaurants and activities."""
    model = AGENT_MODELS["experience"]

    destination = state.get("destination", "Unknown")
    budget = state.get("budget", "Not specified")
    num_travelers = state.get("num_travelers", 1)

    response = model.invoke([
        SystemMessage(content=EXPERIENCE_PROMPT),
        *state["messages"],
        HumanMessage(content=(
            f"Find restaurants and activities in {destination} "
            f"for {num_travelers} traveler(s). Budget: ${budget}."
        )),
    ])

    return {"messages": [response]}
