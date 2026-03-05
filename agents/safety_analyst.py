"""
Travel Research Agency — Safety Analyst Agent
Checks visa requirements, travel advisories, and safety information.
Uses Gemini 2.0 Flash + RAG (Qdrant travel advisories) + MCP tools.
"""

from langchain_core.messages import SystemMessage, HumanMessage
from config import AGENT_MODELS


SAFETY_PROMPT = """You are the Safety Analyst. Check visa requirements, travel
advisories, and safety information for the destination.

Use the check_visa_requirements and get_travel_advisory tools.
Also use RAG context (travel advisories from Qdrant) when provided.

Format your findings as:
📋 VISA: [Requirements for US citizens]
⚠️ ADVISORY LEVEL: [1-4] — [Description]
🏥 HEALTH: [Required/recommended vaccinations]
🚨 SAFETY TIPS: [Key safety information]
📞 EMERGENCY: [Local emergency numbers]

IMPORTANT: Only state facts that are supported by the retrieved context
or tool results. If you're unsure, say so explicitly."""


def safety_analyst_node(state: dict) -> dict:
    """Safety Analyst agent: visa, advisories, safety info + RAG."""
    model = AGENT_MODELS["safety_analyst"]

    destination = state.get("destination", "Unknown")
    rag_context = state.get("rag_context", "")

    # Build context-aware prompt
    context_section = ""
    if rag_context:
        context_section = (
            f"\n\nRETRIEVED TRAVEL ADVISORY CONTEXT:\n{rag_context}\n"
            "Use this context to ground your response. Do NOT make claims "
            "that are not supported by this context."
        )

    response = model.invoke([
        SystemMessage(content=SAFETY_PROMPT + context_section),
        *state["messages"],
        HumanMessage(content=(
            f"Provide safety analysis for traveling to {destination}. "
            f"Check visa requirements, advisories, and health recommendations."
        )),
    ])

    return {"messages": [response]}
