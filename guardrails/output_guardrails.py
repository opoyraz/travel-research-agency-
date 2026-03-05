"""
Travel Research Agency — Output Guardrails (Layer 4)
Rule-based validation of the Writer's final itinerary.
Checks required sections exist and minimum length.
"""

from langchain_core.messages import AIMessage


# Required sections in the final itinerary
REQUIRED_SECTIONS = ["Flight", "Hotel", "Safety"]
MIN_ITINERARY_LENGTH = 200  # characters


def validate_output(state: dict) -> dict:
    """Validate the Writer's final output structure.

    Returns 'output_status': "pass" or "retry".
    If retry, the Writer agent will be re-invoked.
    """
    response = state["messages"][-1].content if state["messages"] else ""

    # Check 1: Required sections exist in the itinerary
    missing = [s for s in REQUIRED_SECTIONS if s.lower() not in response.lower()]

    if missing:
        return {
            "messages": [AIMessage(
                content=f"Itinerary is incomplete — missing: {', '.join(missing)}. "
                        f"Let me compile a complete travel plan."
            )],
            "output_status": "retry",
        }

    # Check 2: Minimum length (avoid empty/stub responses)
    if len(response) < MIN_ITINERARY_LENGTH:
        return {
            "messages": [AIMessage(
                content="The itinerary is too brief. Let me add more detail."
            )],
            "output_status": "retry",
        }

    return {"output_status": "pass"}
