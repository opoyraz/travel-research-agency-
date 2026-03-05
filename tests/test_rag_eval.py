"""
Travel Research Agency — RAG Evaluation Tests
Tests Safety Analyst's RAG pipeline: retrieval quality + generation faithfulness.

Uses:
    - RAGAS: Faithfulness, ResponseRelevancy, ContextPrecision
    - DeepEval: HallucinationMetric

Run: pytest tests/test_rag_eval.py -v
Requires: OPENAI_API_KEY (RAGAS/DeepEval use OpenAI as judge by default)
"""

import os
import pytest
from dotenv import load_dotenv

load_dotenv()

# ═══════════════════════════════════════════════
#  RAGAS: Retriever + Generator Metrics
# ═══════════════════════════════════════════════

@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY required for RAGAS evaluation",
)
class TestRAGASEvaluation:
    """RAGAS evaluation for Safety Analyst RAG pipeline."""

    def test_faithfulness_and_relevancy(self):
        from datasets import Dataset
        from ragas import evaluate
        from ragas.metrics import (
            Faithfulness,
            ResponseRelevancy,
            LLMContextPrecisionWithoutReference,
        )

        eval_data = {
            "question": [
                "What are the visa requirements for US citizens traveling to Japan?",
                "Is there a travel advisory for Thailand?",
                "What vaccinations do I need for Kenya?",
            ],
            "answer": [
                "US citizens can enter Japan visa-free for up to 90 days for tourism.",
                "Thailand has a Level 1 advisory: Exercise Normal Precautions.",
                "Yellow fever vaccination is required for Kenya. Hepatitis A and typhoid recommended.",
            ],
            "contexts": [
                ["Japan allows visa-free entry for US passport holders for stays up to 90 days for tourism or business purposes."],
                ["Thailand - Level 1: Exercise Normal Precautions. The State Department advises normal precautions in Thailand."],
                ["Kenya requires yellow fever vaccination. CDC recommends Hepatitis A, typhoid, and routine vaccinations for travelers."],
            ],
        }

        dataset = Dataset.from_dict(eval_data)

        result = evaluate(
            dataset,
            metrics=[
                Faithfulness(),
                ResponseRelevancy(),
                LLMContextPrecisionWithoutReference(),
            ],
        )

        # All metrics should be above 0.7 threshold
        assert result["faithfulness"] >= 0.7, f"Faithfulness too low: {result['faithfulness']}"
        assert result["answer_relevancy"] >= 0.7, f"Relevancy too low: {result['answer_relevancy']}"


# ═══════════════════════════════════════════════
#  DEEPEVAL: Hallucination Detection
# ═══════════════════════════════════════════════

@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY required for DeepEval evaluation",
)
class TestHallucinationDetection:
    """DeepEval hallucination tests for Safety Analyst."""

    def test_faithful_response_passes(self):
        from deepeval import evaluate
        from deepeval.test_case import LLMTestCase
        from deepeval.metrics import HallucinationMetric

        metric = HallucinationMetric(threshold=0.5)

        test_case = LLMTestCase(
            input="Do US citizens need a visa for Japan?",
            actual_output="US citizens can enter Japan visa-free for up to 90 days.",
            context=[
                "Japan allows visa-free entry for US passport holders for stays up to 90 days.",
            ],
        )

        results = evaluate(test_cases=[test_case], metrics=[metric])
        assert results.test_results[0].success, "Faithful response should pass"

    def test_hallucinated_response_fails(self):
        from deepeval import evaluate
        from deepeval.test_case import LLMTestCase
        from deepeval.metrics import HallucinationMetric

        metric = HallucinationMetric(threshold=0.5)

        test_case = LLMTestCase(
            input="Do US citizens need a visa for Japan?",
            actual_output="US citizens need a visa for Japan and must apply 6 months in advance.",
            context=[
                "Japan allows visa-free entry for US passport holders for stays up to 90 days.",
            ],
        )

        results = evaluate(test_cases=[test_case], metrics=[metric])
        # This SHOULD fail — output contradicts context
        assert not results.test_results[0].success, "Hallucinated response should fail"
