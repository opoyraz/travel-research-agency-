"""
Travel Research Agency — Factuality Guard (Layer 3)
Sync version — checks if Safety Analyst's response is grounded in RAG context.
"""

from langchain_core.messages import SystemMessage, AIMessage
from config import AGENT_MODELS


FACTUALITY_PROMPT = """You are a factuality checker for a travel safety system.

Given the CONTEXT (retrieved documents) and the RESPONSE (agent's answer),
determine if every claim in the RESPONSE is supported by the CONTEXT.

CONTEXT:
{context}

RESPONSE:
{response}

Rules:
1. Every safety claim MUST be traceable to the context
2. Advisory levels and dates MUST match the context
3. If the response adds information NOT in the context, flag it

Respond with ONLY one word: "FAITHFUL" or "HALLUCINATED"
If HALLUCINATED, add a brief note on what was hallucinated."""


def check_factuality(state: dict) -> dict:
    """Check if Safety Analyst's response is grounded in retrieved docs."""
    messages = state.get("messages", [])
    response = messages[-1].content if messages else ""

    rag_context = state.get("rag_context", "No context available")

    guard_llm = AGENT_MODELS["supervisor"]

    result = guard_llm.invoke([
        SystemMessage(content=FACTUALITY_PROMPT.format(
            context=rag_context,
            response=response,
        ))
    ])

    verdict = result.content.strip().upper()

    if "HALLUCINATED" in verdict:
        return {
            "messages": [AIMessage(
                content="⚠️ I need to correct my response. Let me re-check "
                        "the travel advisories and provide verified information only."
            )],
            "factuality_status": "retry",
            "retry_count": state.get("retry_count", 0) + 1,
        }

    return {"factuality_status": "pass"}