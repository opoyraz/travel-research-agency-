"""
Travel Research Agency — Supervisor Agent
Routes user requests to the appropriate specialist agent.
Uses Groq/Llama 3.3 70B for fast routing decisions.
"""

from langchain_core.messages import SystemMessage, AIMessage
from langgraph.types import Command
from config import AGENT_MODELS


SUPERVISOR_PROMPT = """You are the Supervisor of a travel planning agency.
Given the user's request and conversation history, decide which agent to call next.
Available agents: researcher, experience, safety_analyst, budget_optimizer, writer.

Rules:
- Start with researcher + safety_analyst for initial data gathering.
- Call experience after researcher finds destination options.
- Call budget_optimizer after all research is done.
- Call writer LAST to compile the final itinerary.
- If all research is done, route to writer.

Respond with ONLY the next agent name."""

VALID_AGENTS = [
    "researcher",
    "experience",
    "safety_analyst",
    "budget_optimizer",
    "writer",
]


def supervisor_node(state: dict) -> Command:
    """Central supervisor that routes to the next agent."""
    model = AGENT_MODELS["supervisor"]
    response = model.invoke([
        SystemMessage(content=SUPERVISOR_PROMPT),
        *state["messages"],
    ])

    next_agent = response.content.strip().lower()

    # Validate agent name — fallback to researcher if invalid
    if next_agent not in VALID_AGENTS:
        next_agent = "researcher"

    return Command(
        update={"messages": [AIMessage(
            content=f"[Supervisor] Routing to {next_agent}",
            name="supervisor",
        )]},
        goto=next_agent,
    )
