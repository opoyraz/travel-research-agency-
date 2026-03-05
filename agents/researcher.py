"""
Travel Research Agency — Researcher Agent
Finds flights, hotels, and car rentals for the requested trip.
Uses Groq/Llama 3.3 70B + MCP tools (search_flights, search_hotels).
"""

from langchain_core.messages import SystemMessage, HumanMessage
from config import AGENT_MODELS


RESEARCHER_PROMPT = """You are the Travel Researcher. Find flights and hotels
for the requested destination and dates. Use the search_flights and
search_hotels tools. Present ALL options with prices clearly.

Format your findings as:
✈️ FLIGHTS:
- [Airline] [Route] — $[Price] ([Details])

🏨 HOTELS:
- [Hotel Name] — $[Price/night] ([Rating], [Location])

Include at least 3 options for each category when available."""


def researcher_node(state: dict) -> dict:
    """Researcher agent: finds flights and hotels."""
    model = AGENT_MODELS["researcher"]

    destination = state.get("destination", "Unknown")
    travel_dates = state.get("travel_dates", "Not specified")
    budget = state.get("budget", "Not specified")

    response = model.invoke([
        SystemMessage(content=RESEARCHER_PROMPT),
        *state["messages"],
        HumanMessage(content=(
            f"Find flights and hotels to {destination}. "
            f"Dates: {travel_dates}. Budget: ${budget}."
        )),
    ])

    return {"messages": [response]}
