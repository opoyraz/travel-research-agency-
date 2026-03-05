"""
Travel Research Agency — Configuration
Model instances + agent-to-model/tool mappings.
"""

import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_anthropic import ChatAnthropic
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint


load_dotenv()

# ══════════════════════════════════════════
#  MODEL INSTANCES
# ══════════════════════════════════════════

groq_llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0,
    api_key=os.getenv("GROQ_API_KEY"),
)

groq_llm_4 = ChatGroq(
    model="meta-llama/llama-4-scout-17b-16e-instruct",
    temperature=0,
    api_key=os.getenv("GROQ_API_KEY"),
)

# ── HuggingFace (Qwen 2.5 72B — free serverless) ──
hf_llm = HuggingFaceEndpoint(
    repo_id="Qwen/Qwen2.5-72B-Instruct",
    task="text-generation",
    max_new_tokens=1024,
    temperature=0.1,
    huggingfacehub_api_token=os.getenv("HF_TOKEN"),
)
hf_chat = ChatHuggingFace(llm=hf_llm)


claude_llm = ChatAnthropic(
    model="claude-haiku-4-5-20251001",
    temperature=0.3,
    api_key=os.getenv("ANTHROPIC_API_KEY"),
)

# ══════════════════════════════════════════
#  AGENT-TO-MODEL MAPPING
# ══════════════════════════════════════════

AGENT_MODELS = {
    "supervisor":       groq_llm,      # Fast routing decisions
    "researcher":       groq_llm,      # Flights + hotels lookup
    "experience":       groq_llm_4,    # Restaurants + tours
    "safety_analyst":   groq_llm_4,    # Visa + advisory + RAG
    "budget_optimizer": hf_chat,      # Cost analysis + currency
    "writer":           claude_llm,    # Final itinerary prose
}

# ══════════════════════════════════════════
#  AGENT-TO-TOOLS MAPPING (MCP tool names from S3)
# ══════════════════════════════════════════

AGENT_TOOLS = {
    "researcher":       ["search_flights", "search_hotels"],
    "experience":       ["search_restaurants", "search_activities"],
    "safety_analyst":   ["check_visa_requirements", "get_travel_advisory"],
    "budget_optimizer": ["convert_currency"],
    "writer":           [],   # Writer uses no tools — prose only
    "supervisor":       [],   # Supervisor routes only
}


def get_tools_for_agent(agent_name: str, all_tools: list) -> list:
    """Filter MCP tools based on agent's role (least privilege)."""
    allowed = AGENT_TOOLS.get(agent_name, [])
    return [t for t in all_tools if t.name in allowed]
