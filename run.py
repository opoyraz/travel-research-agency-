"""
Travel Research Agency — End-to-End Run Script
Demonstrates the full agent workflow with HITL interrupt/resume.

Usage:
    python run.py

Flow:
    Step 1: Send query → graph runs through guardrails → agents → budget check
    Step 2: Resume from budget check interrupt (approve/replan/cancel)
    Step 3: Resume from final approval interrupt (approve/edit/cancel)
"""

from graph import build_graph
from langgraph.types import Command
from langchain_core.messages import HumanMessage

app = build_graph()


def main():
    config = {
        "configurable": {
            "thread_id": "trip-tokyo-001",
            "user_id": "omar",
        }
    }

    # ══════════════════════════════════════════
    #  Step 1: Send query → runs until first interrupt
    # ══════════════════════════════════════════
    print("═══ Step 1: Initial query ═══")
    result = app.invoke(
        {
            "messages": [HumanMessage(
                content="Plan a 7-day trip to Tokyo, budget $3000"
            )],
            "budget": 3000.0,
            "destination": "Tokyo",
        },
        config=config,
    )

    # Check if we hit an interrupt (budget check or other)
    if "__interrupt__" in result:
        interrupt_info = result["__interrupt__"][0].value
        print(f"⏸️  Paused: {interrupt_info.get('message', 'Awaiting input')}")
        print(f"   Options: {interrupt_info.get('options', [])}")
    else:
        print_result(result)
        return

    # ══════════════════════════════════════════
    #  Step 2: Approve budget
    # ══════════════════════════════════════════
    print("\n═══ Step 2: Budget approval ═══")
    result = app.invoke(Command(resume="approve_anyway"), config=config)

    if "__interrupt__" in result:
        interrupt_info = result["__interrupt__"][0].value
        print(f"⏸️  Paused: {interrupt_info.get('message', 'Awaiting input')}")
        print(f"   Options: {interrupt_info.get('options', [])}")
    else:
        print_result(result)
        return

    # ══════════════════════════════════════════
    #  Step 3: Approve final itinerary
    # ══════════════════════════════════════════
    print("\n═══ Step 3: Final approval ═══")
    result = app.invoke(Command(resume="approve"), config=config)

    print_result(result)


def print_result(result: dict):
    """Print the final result summary."""
    print("\n═══ Complete ═══")
    print(f"Status: {result.get('status', 'unknown')}")
    print(f"Estimated total: ${result.get('estimated_total', 'N/A')}")
    print(f"Messages: {len(result.get('messages', []))}")

    # Print the final itinerary (last AI message)
    messages = result.get("messages", [])
    if messages:
        last_msg = messages[-1]
        print(f"\n{'─' * 60}")
        print("FINAL OUTPUT:")
        print(f"{'─' * 60}")
        print(last_msg.content[:1000])
        if len(last_msg.content) > 1000:
            print(f"\n... ({len(last_msg.content)} total characters)")


if __name__ == "__main__":
    main()
