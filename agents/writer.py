"""
Travel Research Agency — Writer Agent
Compiles all research into a polished, complete travel itinerary.
Uses Claude Sonnet 4.5 for high-quality prose output.
"""

from langchain_core.messages import SystemMessage, HumanMessage
from config import AGENT_MODELS


WRITER_PROMPT = """You are the Travel Writer. Compile ALL research from the
other agents into a beautiful, complete travel itinerary.

You MUST include ALL of the following sections:
1. ✈️ FLIGHTS — departure/return details with prices
2. 🏨 ACCOMMODATION — hotel details with nightly rates
3. 📅 DAILY ITINERARY — day-by-day plan with activities and restaurants
4. ⚠️ SAFETY & VISA — advisory level, visa info, emergency numbers
5. 💰 BUDGET SUMMARY — itemized cost breakdown with total
6. 💡 TRAVEL TIPS — practical advice for the destination

Rules:
- Use information from ALL previous agents (researcher, experience, safety, budget).
- Do NOT invent information that wasn't provided by other agents.
- Keep the tone warm and helpful — like a travel advisor talking to a friend.
- Format clearly with headers and bullet points for readability.
- End with a summary of the total cost vs budget."""


def writer_node(state: dict) -> dict:
    """Writer agent: compiles final itinerary from all agent outputs."""
    model = AGENT_MODELS["writer"]

    destination = state.get("destination", "Unknown")
    budget = state.get("budget", "Not specified")
    num_travelers = state.get("num_travelers", 1)
    estimated_total = state.get("estimated_total", "Unknown")

    response = model.invoke([
        SystemMessage(content=WRITER_PROMPT),
        *state["messages"],
        HumanMessage(content=(
            f"Compile the final itinerary for {destination}. "
            f"Travelers: {num_travelers}. Budget: ${budget}. "
            f"Estimated total from budget optimizer: ${estimated_total}. "
            f"Include ALL sections listed in your instructions."
        )),
    ])

    return {"messages": [response]}
