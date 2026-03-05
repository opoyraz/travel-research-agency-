"""
Travel Research Agency — Input Guardrails (Layer 1)
Rule-based validation: topic relevance, length limits, PII detection.
Fast, no LLM call needed — runs in <1ms.
"""

import re
from langchain_core.messages import HumanMessage, AIMessage


# ═══════════════════════════════════════════════
#  TRAVEL TOPIC KEYWORDS
# ═══════════════════════════════════════════════

TRAVEL_KEYWORDS = {
    "flight", "hotel", "travel", "trip", "visa", "passport",
    "airport", "restaurant", "tour", "booking", "itinerary",
    "destination", "budget", "safety", "currency", "vacation",
    "japan", "tokyo", "paris", "london", "brazil", "thailand",
    "france", "car rental", "insurance", "advisory", "embassy",
}

MAX_INPUT_LENGTH = 2000  # characters
MIN_INPUT_LENGTH = 5     # characters


# ═══════════════════════════════════════════════
#  PII DETECTION
# ═══════════════════════════════════════════════

PII_PATTERNS = {
    "credit_card": re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b"),
    "us_passport": re.compile(r"\b[A-Z]\d{8}\b"),
    "phone": re.compile(r"\b(?:\+1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
}


def detect_pii(text: str) -> list[str]:
    """Return list of PII types detected in text."""
    found = []
    for pii_type, pattern in PII_PATTERNS.items():
        if pattern.search(text):
            found.append(pii_type)
    return found


# ═══════════════════════════════════════════════
#  INPUT GUARD NODE
# ═══════════════════════════════════════════════

def validate_input(state: dict) -> dict:
    """Input guardrail node — validates user query before processing.

    Returns state with 'guardrail_status' key:
      - "pass": query is valid, continue to injection guard
      - "block": query is invalid, return error to user
    """
    messages = state["messages"]

    # Get the latest user message
    user_msg = None
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            user_msg = msg.content
            break

    if not user_msg:
        return {
            "messages": [AIMessage(content="Please provide a travel-related question.")],
            "guardrail_status": "block",
        }

    # Check 1: Too short
    if len(user_msg.strip()) < MIN_INPUT_LENGTH:
        return {
            "messages": [AIMessage(
                content="Your question is too short. Please describe your travel plans."
            )],
            "guardrail_status": "block",
        }

    # Check 2: Too long (possible abuse)
    if len(user_msg) > MAX_INPUT_LENGTH:
        return {
            "messages": [AIMessage(
                content="Your message is too long. Please keep it under 2000 characters."
            )],
            "guardrail_status": "block",
        }

    # Check 3: Topic relevance
    query_lower = user_msg.lower()
    is_travel = any(kw in query_lower for kw in TRAVEL_KEYWORDS)
    if not is_travel:
        return {
            "messages": [AIMessage(
                content="I'm a travel planning assistant. "
                        "Please ask me about flights, hotels, safety, "
                        "or destinations and I'll help you plan your trip!"
            )],
            "guardrail_status": "block",
        }

    # Check 4: PII detection
    pii_found = detect_pii(user_msg)
    if pii_found:
        return {
            "messages": [AIMessage(
                content=f"⚠️ I detected sensitive personal information "
                        f"({', '.join(pii_found)}) in your message. "
                        f"Please remove it and resend your request."
            )],
            "guardrail_status": "block",
        }

    # All checks passed
    return {"guardrail_status": "pass"}
