"""
Travel Research Agency — Budget Optimizer Agent
Analyzes costs, finds savings, and converts currency.
Uses Groq/Llama 3.3 70B + MCP tool (convert_currency).
"""

from langchain_core.messages import SystemMessage, HumanMessage
from config import AGENT_MODELS


BUDGET_PROMPT = """You are the Budget Optimizer. Analyze the trip costs from
the researcher and experience agents. Create a detailed cost breakdown
and find ways to save money.

Use the convert_currency tool to show costs in local currency.

Format your output as:
💰 COST BREAKDOWN:
- Flights: $[amount]
- Hotels ([nights] nights): $[amount]
- Activities: $[amount]
- Food (estimated): $[amount]
- Transportation (local): $[amount]
- Miscellaneous: $[amount]
─────────────────
TOTAL: $[amount] / Budget: $[budget]

💡 SAVINGS TIPS:
- [Specific suggestion with estimated savings]

📊 LOCAL CURRENCY: [Total] = [Amount in local currency]

Flag if total exceeds the user's budget."""


def budget_optimizer_node(state: dict) -> dict:
    """Budget Optimizer agent: cost analysis + savings."""
    model = AGENT_MODELS["budget_optimizer"]

    budget = state.get("budget", 0)
    destination = state.get("destination", "Unknown")

    response = model.invoke([
        SystemMessage(content=BUDGET_PROMPT),
        *state["messages"],
        HumanMessage(content=(
            f"Analyze and optimize the trip budget for {destination}. "
            f"User budget: ${budget}. Review all costs from previous agents."
        )),
    ])

    # Extract estimated total (simple heuristic — production would parse structured output)
    estimated_total = budget * 0.9  # placeholder
    try:
        content = response.content
        if "TOTAL:" in content:
            import re
            match = re.search(r"TOTAL:\s*\$?([\d,]+\.?\d*)", content)
            if match:
                estimated_total = float(match.group(1).replace(",", ""))
    except (ValueError, AttributeError):
        pass

    return {
        "messages": [response],
        "estimated_total": estimated_total,
        "cost_breakdown": {"raw": response.content},
    }
