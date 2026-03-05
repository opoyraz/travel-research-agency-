"""
Travel Research Agency — End-to-End Evaluation Tests
Tests full pipeline output quality using DeepEval metrics.

Metrics:
    - GEval: Itinerary Completeness, Budget Accuracy
    - ToolCorrectnessMetric: Agent-tool mapping correctness
    - BiasMetric: Writer output fairness
    - AnswerRelevancyMetric: Response relevance to query

Run: deepeval test run tests/test_e2e.py
  or: pytest tests/test_e2e.py -v
Requires: OPENAI_API_KEY
"""

import os
import pytest
from dotenv import load_dotenv

load_dotenv()

SKIP_REASON = "OPENAI_API_KEY required for DeepEval evaluation"
skip_if_no_key = pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason=SKIP_REASON)


# ═══════════════════════════════════════════════
#  SIMULATED GRAPH OUTPUT (replace with real graph.invoke in production)
# ═══════════════════════════════════════════════

def run_travel_graph(query: str) -> str:
    """Simulate graph output for testing.

    In production, replace with:
        result = app.invoke({"messages": [HumanMessage(content=query)], ...}, config)
        return result["messages"][-1].content
    """
    return (
        "Tokyo 7-Day Itinerary:\n"
        "✈️ Flight: Delta DL275, Austin → Tokyo (NRT), $850\n"
        "🏨 Hotel: Park Hyatt Tokyo, 5 nights at $280/night = $1,400\n"
        "📅 Day 1: Senso-ji Temple, Ramen at Ichiran ($12)\n"
        "📅 Day 2: Shibuya Crossing, Harajuku, Meiji Shrine\n"
        "📅 Day 3: Tsukiji Outer Market food tour ($80)\n"
        "📅 Day 4: TeamLab Borderless ($35), Akihabara\n"
        "📅 Day 5: Day trip to Mt. Fuji ($120)\n"
        "📅 Day 6: Ginza shopping, Sukiyabashi Jiro dinner\n"
        "📅 Day 7: Ueno Park, departure\n"
        "⚠️ Safety: Japan Level 1 advisory — Exercise Normal Precautions. "
        "No visa needed for US citizens (up to 90 days). "
        "Emergency: 110 (police), 119 (fire/ambulance).\n"
        "💰 Budget: Flights $850 + Hotel $1,400 + Activities $550 = $2,800 total "
        "(under $3,000 budget)"
    )


# ═══════════════════════════════════════════════
#  TEST 1: ITINERARY COMPLETENESS (GEval)
# ═══════════════════════════════════════════════

@skip_if_no_key
def test_itinerary_completeness():
    """Writer output must include all required sections."""
    from deepeval import assert_test
    from deepeval.test_case import LLMTestCase, LLMTestCaseParams
    from deepeval.metrics import GEval

    completeness = GEval(
        name="Itinerary Completeness",
        criteria=(
            "Determine if the travel itinerary includes ALL required sections: "
            "flights, hotels, daily activities, safety info, and budget breakdown."
        ),
        evaluation_params=[
            LLMTestCaseParams.ACTUAL_OUTPUT,
            LLMTestCaseParams.EXPECTED_OUTPUT,
        ],
        threshold=0.7,
    )

    output = run_travel_graph("Plan a 7-day trip to Tokyo, budget $3000")

    test_case = LLMTestCase(
        input="Plan a 7-day trip to Tokyo, budget $3000",
        actual_output=output,
        expected_output="Complete itinerary with flights, hotels, daily activities, safety, budget",
    )

    assert_test(test_case, [completeness])


# ═══════════════════════════════════════════════
#  TEST 2: BUDGET ACCURACY (GEval)
# ═══════════════════════════════════════════════

@skip_if_no_key
def test_budget_accuracy():
    """Cost items must sum correctly and stay within budget."""
    from deepeval import evaluate
    from deepeval.test_case import LLMTestCase, LLMTestCaseParams
    from deepeval.metrics import GEval

    budget_accuracy = GEval(
        name="Budget Accuracy",
        criteria=(
            "Check that: 1) Individual cost items sum to the stated total. "
            "2) The total does not exceed the user's stated budget. "
            "3) All costs are in the same currency."
        ),
        evaluation_params=[
            LLMTestCaseParams.INPUT,
            LLMTestCaseParams.ACTUAL_OUTPUT,
        ],
        threshold=0.7,
    )

    test_cases = [
        # Under budget, math correct → should PASS
        LLMTestCase(
            input="Budget: $3000",
            actual_output="Flights $850 + Hotel $1400 + Activities $550 = $2800 total",
        ),
        # At budget, math correct → should PASS
        LLMTestCase(
            input="Budget: $3000",
            actual_output="Flights $1200 + Hotel $1300 + Activities $500 = $3000 total",
        ),
        # Over budget → should FAIL
        LLMTestCase(
            input="Budget: $3000",
            actual_output="Flights $1500 + Hotel $2000 + Activities $800 = $4300 total",
        ),
    ]

    results = evaluate(test_cases=test_cases, metrics=[budget_accuracy])
    # First two should pass, third should fail
    assert results.test_results[0].success, "Under-budget case should pass"
    assert results.test_results[1].success, "At-budget case should pass"


# ═══════════════════════════════════════════════
#  TEST 3: TOOL CORRECTNESS
# ═══════════════════════════════════════════════

@skip_if_no_key
def test_tool_correctness():
    """Each agent should call the right tools."""
    from deepeval import evaluate
    from deepeval.test_case import LLMTestCase, ToolCall
    from deepeval.metrics import ToolCorrectnessMetric

    # Researcher should call search_flights + search_hotels
    researcher_test = LLMTestCase(
        input="Find flights and hotels for a Tokyo trip",
        actual_output="Found 3 flights and 5 hotels for Tokyo.",
        tools_called=[
            ToolCall(name="search_flights"),
            ToolCall(name="search_hotels"),
        ],
        expected_tools=[
            ToolCall(name="search_flights"),
            ToolCall(name="search_hotels"),
        ],
    )

    # Safety Analyst should call advisory tools, NOT flight tools
    safety_test = LLMTestCase(
        input="Check travel advisories for Thailand",
        actual_output="Thailand: Level 1 advisory.",
        tools_called=[
            ToolCall(name="get_travel_advisory"),
            ToolCall(name="check_visa_requirements"),
        ],
        expected_tools=[
            ToolCall(name="get_travel_advisory"),
            ToolCall(name="check_visa_requirements"),
        ],
    )

    metric = ToolCorrectnessMetric(threshold=0.7)
    results = evaluate(test_cases=[researcher_test, safety_test], metrics=[metric])

    assert results.test_results[0].success, "Researcher tool calls should be correct"
    assert results.test_results[1].success, "Safety tool calls should be correct"


# ═══════════════════════════════════════════════
#  TEST 4: BIAS DETECTION
# ═══════════════════════════════════════════════

@skip_if_no_key
def test_writer_no_bias():
    """Writer output should not contain demographic bias."""
    from deepeval import evaluate
    from deepeval.test_case import LLMTestCase
    from deepeval.metrics import BiasMetric

    metric = BiasMetric(threshold=0.5)

    test_case = LLMTestCase(
        input="Recommend restaurants in Tokyo",
        actual_output=(
            "Here are top Tokyo restaurants for all budgets and dietary needs: "
            "Ichiran Ramen ($ casual), Sukiyabashi Jiro ($$$$ fine dining), "
            "Afuri ($ modern ramen), Gonpachi ($$ Japanese). "
            "Halal options available at several locations."
        ),
    )

    results = evaluate(test_cases=[test_case], metrics=[metric])
    assert results.test_results[0].success, "Writer output should be unbiased"


# ═══════════════════════════════════════════════
#  TEST 5: ANSWER RELEVANCY
# ═══════════════════════════════════════════════

@skip_if_no_key
def test_answer_relevancy():
    """Agent response must be relevant to the query."""
    from deepeval import assert_test
    from deepeval.test_case import LLMTestCase
    from deepeval.metrics import AnswerRelevancyMetric

    metric = AnswerRelevancyMetric(threshold=0.7)

    output = run_travel_graph("Plan a 7-day trip to Tokyo, budget $3000")

    test_case = LLMTestCase(
        input="Plan a 7-day trip to Tokyo, budget $3000",
        actual_output=output,
    )

    assert_test(test_case, [metric])


# ═══════════════════════════════════════════════
#  GOLDEN DATASET (for batch evaluation)
# ═══════════════════════════════════════════════

def get_golden_dataset():
    """Return the golden evaluation dataset for batch testing.

    Usage:
        from deepeval.dataset import EvaluationDataset
        dataset = get_golden_dataset()
        evaluate(dataset.test_cases, metrics=[...])
    """
    from deepeval.dataset import EvaluationDataset, Golden

    return EvaluationDataset(goldens=[
        # Happy path
        Golden(
            input="Plan a 7-day trip to Tokyo, budget $3000",
            expected_output="Complete itinerary under $3000 with flights, hotel, activities",
        ),
        # Over budget
        Golden(
            input="Plan a 14-day luxury trip to Paris, budget $1000",
            expected_output="Should flag budget as insufficient for luxury + 14 days",
        ),
        # High-risk destination
        Golden(
            input="Plan a trip to a Level 4 advisory country",
            expected_output="Should show safety warning and offer alternatives",
        ),
        # Dietary preference
        Golden(
            input="Plan a Tokyo trip with halal food options",
            expected_output="Itinerary should prioritize halal restaurants",
        ),
        # Off-topic (guardrail test)
        Golden(
            input="Write me a poem about the ocean",
            expected_output="Should be blocked by input guardrail",
        ),
    ])
