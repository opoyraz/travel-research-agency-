"""
Travel Research Agency — Guardrail Unit Tests
Tests input validation and output validation (rule-based, no LLM needed).

Run: pytest tests/test_guardrails.py -v
"""

import pytest
from langchain_core.messages import HumanMessage, AIMessage

from guardrails.input_guardrails import validate_input, detect_pii
from guardrails.output_guardrails import validate_output


# ═══════════════════════════════════════════════
#  LAYER 1: INPUT GUARD
# ═══════════════════════════════════════════════

class TestInputGuard:
    """Test rule-based input validation."""

    def test_travel_query_passes(self):
        result = validate_input({"messages": [HumanMessage(content="Find flights to Tokyo")]})
        assert result["guardrail_status"] == "pass"

    def test_off_topic_blocked(self):
        result = validate_input({"messages": [HumanMessage(content="How to cook pasta?")]})
        assert result["guardrail_status"] == "block"

    def test_too_short_blocked(self):
        result = validate_input({"messages": [HumanMessage(content="hi")]})
        assert result["guardrail_status"] == "block"

    def test_too_long_blocked(self):
        result = validate_input({"messages": [HumanMessage(content="flight " * 500)]})
        assert result["guardrail_status"] == "block"

    def test_empty_messages_blocked(self):
        result = validate_input({"messages": []})
        assert result["guardrail_status"] == "block"

    def test_pii_credit_card_blocked(self):
        result = validate_input({
            "messages": [HumanMessage(
                content="Book a flight with card 4111-1111-1111-1111"
            )]
        })
        assert result["guardrail_status"] == "block"

    def test_pii_ssn_blocked(self):
        result = validate_input({
            "messages": [HumanMessage(
                content="My passport travel SSN is 123-45-6789 for the trip"
            )]
        })
        assert result["guardrail_status"] == "block"

    def test_budget_query_passes(self):
        result = validate_input({
            "messages": [HumanMessage(content="What's a good budget for a trip to Paris?")]
        })
        assert result["guardrail_status"] == "pass"

    def test_safety_query_passes(self):
        result = validate_input({
            "messages": [HumanMessage(content="Is it safe to travel to Brazil right now?")]
        })
        assert result["guardrail_status"] == "pass"


# ═══════════════════════════════════════════════
#  PII DETECTION
# ═══════════════════════════════════════════════

class TestPIIDetection:
    """Test PII pattern matching."""

    def test_credit_card_detected(self):
        assert "credit_card" in detect_pii("My card is 4111-1111-1111-1111")

    def test_ssn_detected(self):
        assert "ssn" in detect_pii("SSN: 123-45-6789")

    def test_phone_detected(self):
        assert "phone" in detect_pii("Call me at (512) 555-1234")

    def test_passport_detected(self):
        assert "us_passport" in detect_pii("Passport: A12345678")

    def test_clean_text_no_pii(self):
        assert detect_pii("Book a flight to Tokyo for 7 days") == []

    def test_numbers_in_context_not_flagged(self):
        # Budget amounts should NOT trigger credit card detection
        assert detect_pii("My budget is $3000") == []


# ═══════════════════════════════════════════════
#  LAYER 4: OUTPUT GUARD
# ═══════════════════════════════════════════════

class TestOutputGuard:
    """Test output validation (checks itinerary completeness)."""

    def test_complete_itinerary_passes(self):
        complete = (
            "✈️ Flight: Delta DL275, $850 from Austin to Tokyo\n"
            "🏨 Hotel: Park Hyatt Tokyo, 5 nights at $280/night\n"
            "⚠️ Safety: Japan Level 1 advisory. No visa needed for US citizens. "
            "Emergency: 110 for police, 119 for ambulance.\n"
            "💰 Budget: $850 + $1,400 + $550 = $2,800 total"
        )
        result = validate_output({"messages": [AIMessage(content=complete)]})
        assert result["output_status"] == "pass"

    def test_missing_safety_retries(self):
        incomplete = (
            "✈️ Flight: Delta DL275, $850\n"
            "🏨 Hotel: Park Hyatt Tokyo, 5 nights at $280/night"
        )
        result = validate_output({"messages": [AIMessage(content=incomplete)]})
        assert result["output_status"] == "retry"

    def test_too_short_retries(self):
        stub = "Flight: $850. Hotel: $280. Safety: Level 1."
        result = validate_output({"messages": [AIMessage(content=stub)]})
        assert result["output_status"] == "retry"

    def test_empty_output_retries(self):
        result = validate_output({"messages": [AIMessage(content="")]})
        assert result["output_status"] == "retry"
