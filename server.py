"""
Travel Research Agency — FastAPI Server
Serves the LangGraph agent graph over HTTP with SSE streaming.

Endpoints:
    GET  /health             → readiness check
    POST /plan               → sync trip planning (waits for full result)
    POST /stream             → SSE streaming (real-time node updates)
    POST /resume             → resume from HITL interrupt
    GET  /status/{thread_id} → check trip planning status

Run:
    uvicorn server:app --host 0.0.0.0 --port 8000 --reload
"""

import uuid
import json
import asyncio
from collections.abc import AsyncIterable
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from langgraph.types import Command

from schemas import (
    TripRequest,
    TripResponse,
    ResumeRequest,
    StatusResponse,
    HealthResponse,
)
from graph import build_graph

load_dotenv()


# ══════════════════════════════════════════
#  LIFESPAN: Initialize graph once at startup
# ══════════════════════════════════════════

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Build the graph once and attach to app.state."""
    app.state.graph = build_graph()
    yield


app = FastAPI(
    title="Travel Research Agency",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS (allow React/Next.js frontend) ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_methods=["*"],
    allow_headers=["*"],
)


# ══════════════════════════════════════════
#  HELPER: Timeout wrapper
# ══════════════════════════════════════════

async def invoke_with_timeout(graph, inputs, config, timeout=60):
    """Wrap graph.ainvoke with a timeout to prevent runaway agents."""
    try:
        return await asyncio.wait_for(
            graph.ainvoke(inputs, config=config),
            timeout=timeout,
        )
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=504,
            detail=f"Agent did not respond within {timeout}s",
        )


# ══════════════════════════════════════════
#  HELPER: Check if graph is at an interrupt
# ══════════════════════════════════════════

async def is_interrupted(graph, config: dict) -> bool:
    """Check if the graph is paused at an HITL interrupt."""
    state = await graph.aget_state(config)
    return bool(state.tasks and any(t.interrupts for t in state.tasks))


# ══════════════════════════════════════════
#  ENDPOINTS
# ══════════════════════════════════════════

@app.get("/health", response_model=HealthResponse)
async def health():
    """Readiness check for load balancers and Kubernetes probes."""
    return HealthResponse()


@app.post("/plan", response_model=TripResponse)
async def plan_trip(request: TripRequest):
    """Plan a trip (sync — waits for full result or first HITL interrupt)."""
    thread_id = request.thread_id or str(uuid.uuid4())
    config = {
        "configurable": {"thread_id": thread_id, "user_id": "api-user"},
        "tags": ["api", request.destination or "unknown"],
    }

    result = await invoke_with_timeout(
        app.state.graph,
        {
            "messages": [HumanMessage(content=request.query)],
            "budget": request.budget,
            "destination": request.destination,
            "num_travelers": request.num_travelers,
        },
        config=config,
    )

    interrupted = await is_interrupted(app.state.graph, config)

    return TripResponse(
        thread_id=thread_id,
        status="awaiting_approval" if interrupted else "complete",
        itinerary=result["messages"][-1].content if not interrupted else None,
        estimated_total=result.get("estimated_total"),
        message_count=len(result["messages"]),
    )


@app.post("/resume", response_model=TripResponse)
async def resume_trip(request: ResumeRequest):
    """Resume from HITL interrupt (budget check or final approval)."""
    config = {"configurable": {"thread_id": request.thread_id}}

    # Verify thread exists and is interrupted
    state = await app.state.graph.aget_state(config)
    if not state.values:
        raise HTTPException(status_code=404, detail="Trip not found")

    result = await invoke_with_timeout(
        app.state.graph,
        Command(resume=request.decision),
        config=config,
    )

    interrupted = await is_interrupted(app.state.graph, config)

    return TripResponse(
        thread_id=request.thread_id,
        status="awaiting_approval" if interrupted else result.get("status", "complete"),
        itinerary=result["messages"][-1].content if not interrupted else None,
        estimated_total=result.get("estimated_total"),
        message_count=len(result["messages"]),
    )


@app.post("/stream")
async def stream_trip(request: TripRequest):
    """Stream trip planning via Server-Sent Events (SSE).

    Events:
        init          → {thread_id}
        node_update   → {node, has_messages}
        interrupt     → {type, message, options}
        done          → {thread_id}
    """
    thread_id = request.thread_id or str(uuid.uuid4())
    config = {
        "configurable": {"thread_id": thread_id, "user_id": "api-user"},
    }

    async def event_generator() -> AsyncIterable[str]:
        # Send thread_id first so client can resume later
        yield f"data: {json.dumps({'type': 'init', 'thread_id': thread_id})}\n\n"

        async for event, metadata in app.state.graph.astream(
            {
                "messages": [HumanMessage(content=request.query)],
                "budget": request.budget,
                "destination": request.destination,
                "num_travelers": request.num_travelers,
            },
            config=config,
            stream_mode="updates",
        ):
            # Each event is {node_name: {state_updates}}
            for node_name, updates in event.items():
                payload = {
                    "type": "node_update",
                    "node": node_name,
                    "has_messages": "messages" in updates,
                }
                yield f"data: {json.dumps(payload)}\n\n"

        # Check if we stopped at an interrupt
        interrupted = await is_interrupted(app.state.graph, config)
        if interrupted:
            state = await app.state.graph.aget_state(config)
            interrupt_value = state.tasks[0].interrupts[0].value if state.tasks else {}
            yield f"data: {json.dumps({'type': 'interrupt', **interrupt_value})}\n\n"

        # Send completion event
        yield f"data: {json.dumps({'type': 'done', 'thread_id': thread_id})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/status/{thread_id}", response_model=StatusResponse)
async def get_trip_status(thread_id: str):
    """Check trip planning status (useful for polling after async operations)."""
    config = {"configurable": {"thread_id": thread_id}}

    state = await app.state.graph.aget_state(config)

    if not state.values:
        raise HTTPException(status_code=404, detail="Trip not found")

    interrupted = bool(
        state.tasks and any(t.interrupts for t in state.tasks)
    )

    return StatusResponse(
        thread_id=thread_id,
        status=state.values.get("status", "active"),
        estimated_total=state.values.get("estimated_total"),
        awaiting_approval=interrupted,
        message_count=len(state.values.get("messages", [])),
    )
