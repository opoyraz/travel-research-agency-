"""
Travel Research Agency — Full Graph Assembly
Wires all 14 nodes from Sections 2-7 into a single LangGraph StateGraph.

Node flow:
  START → load_user_prefs → input_guard → injection_guard → supervisor
  supervisor → {researcher, experience, safety_analyst, budget_optimizer, writer}
  safety_analyst → factuality_guard → (retry safety OR supervisor)
  budget_optimizer → budget_check (HITL) → writer
  writer → final_approval (HITL) → output_guard → save_preferences → END
"""

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore

from state import TravelState

from agents import (
    supervisor_node,
    researcher_node,
    experience_node,
    safety_analyst_node,
    budget_optimizer_node,
    writer_node,
)

from guardrails.input_guardrails import validate_input
from guardrails.injection_guard import check_prompt_injection
from guardrails.factuality_guard import check_factuality
from guardrails.output_guardrails import validate_output

from memory.user_context import load_user_context, save_preferences

from hitl.budget_check import budget_check_node
from hitl.final_approval import final_approval_node

from routing import (
    route_after_input_guard,
    route_after_injection,
    route_after_factuality,
    route_after_budget_check,
    route_after_final_approval,
    route_after_output_guard,
)


def build_graph(
    checkpointer=None,
    store=None,
):
    """Build and compile the full travel agency graph.

    Args:
        checkpointer: Short-term memory (per-thread). Defaults to InMemorySaver.
        store: Long-term memory (cross-thread). Defaults to InMemoryStore.

    Returns:
        Compiled LangGraph application ready for .invoke() or .astream().
    """

    # ══════════════════════════════════════════
    #  REGISTER ALL 14 NODES
    # ══════════════════════════════════════════
    graph = StateGraph(TravelState)

    # Memory (S6)
    graph.add_node("load_user_prefs", load_user_context)
    graph.add_node("save_preferences", save_preferences)

    # Guardrails (S5)
    graph.add_node("input_guard", validate_input)
    graph.add_node("injection_guard", check_prompt_injection)
    graph.add_node("factuality_guard", check_factuality)
    graph.add_node("output_guard", validate_output)

    # Agents (S2)
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("researcher", researcher_node)
    graph.add_node("experience", experience_node)
    graph.add_node("safety_analyst", safety_analyst_node)
    graph.add_node("budget_optimizer", budget_optimizer_node)
    graph.add_node("writer", writer_node)

    # HITL (S7)
    graph.add_node("budget_check", budget_check_node)
    graph.add_node("final_approval", final_approval_node)

    # ══════════════════════════════════════════
    #  WIRE ALL EDGES
    # ══════════════════════════════════════════

    # ── Entry pipeline ──
    graph.add_edge(START, "load_user_prefs")
    graph.add_edge("load_user_prefs", "input_guard")

    # ── Input guard → injection guard or END ──
    graph.add_conditional_edges("input_guard", route_after_input_guard, {
        "injection_guard": "injection_guard",
        "__end__": END,
    })

    # ── Injection guard → supervisor or END ──
    graph.add_conditional_edges("injection_guard", route_after_injection, {
        "supervisor": "supervisor",
        "__end__": END,
    })

    # ── Supervisor routes dynamically via Command(goto=...) ──
    # No explicit edges from supervisor needed — Command handles it

    # ── Worker agents report back to supervisor ──
    graph.add_edge("researcher", "supervisor")
    graph.add_edge("experience", "supervisor")

    # ── Safety → factuality check first ──
    graph.add_edge("safety_analyst", "factuality_guard")

    # ── Factuality guard → retry safety OR back to supervisor ──
    graph.add_conditional_edges("factuality_guard", route_after_factuality, {
        "safety_analyst": "safety_analyst",
        "supervisor": "supervisor",
    })

    # ── Budget optimizer → HITL budget check ──
    graph.add_edge("budget_optimizer", "budget_check")

    # ── Budget check → writer OR replan OR end ──
    graph.add_conditional_edges("budget_check", route_after_budget_check, {
        "writer": "writer",
        "budget_optimizer": "budget_optimizer",
        "__end__": END,
    })

    # ── Writer → HITL final approval ──
    graph.add_edge("writer", "final_approval")

    # ── Final approval → output guard OR rewrite OR end ──
    graph.add_conditional_edges("final_approval", route_after_final_approval, {
        "output_guard": "output_guard",
        "writer": "writer",
        "__end__": END,
    })

    # ── Output guard → save preferences OR retry writer ──
    graph.add_conditional_edges("output_guard", route_after_output_guard, {
        "writer": "writer",
        "save_preferences": "save_preferences",
    })

    # ── Exit ──
    graph.add_edge("save_preferences", END)

    # ══════════════════════════════════════════
    #  COMPILE WITH BOTH MEMORY SYSTEMS
    # ══════════════════════════════════════════
    return graph.compile(
        #checkpointer=checkpointer or InMemorySaver(),
        store=store or InMemoryStore(),
    )

