"""
Travel Research Agency — Chainlit UI
Run: chainlit run chainlit_app.py -w
"""

import uuid
import re
import chainlit as cl
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

from graph import build_graph

load_dotenv()


@cl.on_chat_start
async def on_chat_start():
    graph = build_graph()
    thread_id = str(uuid.uuid4())
    cl.user_session.set("graph", graph)
    cl.user_session.set("thread_id", thread_id)

    await cl.Message(
        content=(
            "## ✈️ Travel Research Agency\n\n"
            "I'm your AI travel planner with **6 specialist agents**:\n\n"
            "- **Researcher** — flights & hotels\n"
            "- **Experience Planner** — restaurants & activities\n"
            "- **Safety Analyst** — visa, advisories, health\n"
            "- **Budget Optimizer** — cost analysis & savings\n"
            "- **Writer** — compiles your final itinerary\n"
            "- **Supervisor** — orchestrates everything\n\n"
            "Try: *\"Plan a 7-day trip to Tokyo on a $3000 budget\"*"
        ),
    ).send()


@cl.set_starters
async def set_starters():
    return [
        cl.Starter(label="Tokyo 7-day trip", message="Plan a 7-day trip to Tokyo for 2 people, budget $3000"),
        cl.Starter(label="Paris weekend getaway", message="Plan a 3-day romantic weekend in Paris, budget $2000"),
        cl.Starter(label="Bangkok on a budget", message="Plan a 5-day budget trip to Bangkok, max $1500"),
        cl.Starter(label="Barcelona family trip", message="Plan a 5-day family trip to Barcelona for 4 people, budget $5000"),
    ]


@cl.on_message
async def on_message(message: cl.Message):
    graph = cl.user_session.get("graph")
    thread_id = cl.user_session.get("thread_id")

    config = {"configurable": {"thread_id": thread_id}}

    msg_lower = message.content.lower()

    budget_match = re.search(r"\$\s?([\d,]+)", message.content)
    budget = float(budget_match.group(1).replace(",", "")) if budget_match else None

    dest_match = re.search(r"(?:to|in|visit)\s+([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)", message.content)
    destination = dest_match.group(1) if dest_match else None

    travelers_match = re.search(r"(\d+)\s*(?:people|person|travelers|travellers)", msg_lower)
    num_travelers = int(travelers_match.group(1)) if travelers_match else 1

    inputs = {
        "messages": [HumanMessage(content=message.content)],
        "budget": budget,
        "destination": destination,
        "num_travelers": num_travelers,
    }

    thinking_msg = cl.Message(content="⏳ Planning your trip... this may take a minute.")
    await thinking_msg.send()

    try:
        result = await graph.ainvoke(inputs, config=config)

        messages = result.get("messages", [])
        if messages:
            await cl.Message(content=messages[-1].content).send()
        else:
            await cl.Message(content="Trip planning complete but no output was generated.").send()

    except Exception as e:
        import traceback
        traceback.print_exc()
        await cl.Message(content=f"❌ Error: {str(e)}").send()