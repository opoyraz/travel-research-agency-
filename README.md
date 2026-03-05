# Travel Research Agency

A production-grade multi-agent travel planning system built with LangGraph. Six specialist AI agents collaborate to research flights, hotels, activities, safety info, and budget — then compile a complete travel itinerary.

Built as a portfolio project demonstrating end-to-end AI engineering: multi-agent orchestration, guardrails, RAG, human-in-the-loop, observability, and containerized deployment.

## Architecture

```
USER QUERY
     │
     ▼
┌─────────────────────────────────────────────────────┐
│                   CHAINLIT UI                        │
│              (Chat + Agent Progress)                 │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│                 LANGGRAPH GRAPH                      │
│                                                      │
│  load_prefs → input_guard → injection_guard          │
│       → SUPERVISOR                                   │
│         ├── Researcher        (Groq / Llama 3.3)     │
│         ├── Experience        (Groq / Llama 4 Scout) │
│         ├── Safety Analyst    (Groq / Llama 4 Scout) │
│         ├── Budget Optimizer  (HuggingFace / Qwen)   │
│         └── Writer            (Claude Haiku 4.5)     │
│       → factuality_guard → budget_check              │
│       → final_approval → output_guard → save_prefs   │
│                                                      │
│  ┌──────────────┐    ┌─────────────────────┐        │
│  │  MCP TOOLS   │    │   QDRANT (RAG)      │        │
│  │  (FastMCP)   │    │   + Jina v3 Embed   │        │
│  └──────────────┘    └─────────────────────┘        │
│                                                      │
│  LangSmith Tracing  │  RAGAS + DeepEval Eval        │
└──────────────────────────────────────────────────────┘
```

## Multi-Provider Strategy

Each agent uses the model best suited to its task:

| Agent | Provider | Model | Why |
|---|---|---|---|
| Supervisor | Groq | Llama 3.3 70B | Fast routing decisions |
| Researcher | Groq | Llama 3.3 70B | Flights & hotels search |
| Experience | Groq | Llama 4 Scout | Restaurants & activities |
| Safety Analyst | Groq | Llama 4 Scout | Visa & advisory + RAG |
| Budget Optimizer | HuggingFace | Qwen 2.5 72B | Cost analysis (free serverless) |
| Writer | Anthropic | Claude Haiku 4.5 | High-quality prose |

## Live API Integrations

All travel data comes from real APIs — zero mock data:

| Tool | API Source | Engine |
|---|---|---|
| `search_flights` | SerpAPI | Google Flights |
| `search_hotels` | SerpAPI | Google Hotels |
| `search_activities` | SerpAPI | Google Local |
| `search_restaurants` | SerpAPI | Google Local |
| `check_visa_requirements` | SerpAPI | Google Search |
| `get_travel_advisory` | SerpAPI | Google Search |
| `convert_currency` | SerpAPI | Google Answer Box |
| `get_weather` | OpenWeatherMap | Current Weather API |

## Project Structure

```
travel-research-agency/
├── chainlit_app.py          # Chainlit chat UI
├── server.py                # FastAPI (5 endpoints + SSE)
├── graph.py                 # Full 14-node LangGraph assembly
├── state.py                 # TravelState TypedDict
├── config.py                # Multi-provider model config
├── routing.py               # Conditional edge functions
├── schemas.py               # Pydantic request/response models
├── run.py                   # CLI demo
├── requirements.txt
├── .env.example
├── Dockerfile
├── docker-compose.yml
│
├── agents/
│   ├── supervisor.py        # Routes to specialists (Groq)
│   ├── researcher.py        # Flights + hotels (Groq)
│   ├── experience.py        # Restaurants + activities (Llama 4)
│   ├── safety_analyst.py    # Visa + advisories + RAG (Llama 4)
│   ├── budget_optimizer.py  # Cost analysis (HuggingFace)
│   └── writer.py            # Final itinerary (Claude)
│
├── tools/
│   └── mcp_server.py        # FastMCP — 8 tools via SerpAPI + OpenWeatherMap
│
├── rag/
│   ├── documents.py         # Travel advisory data
│   ├── ingest.py            # Chunk → Jina v3 embed → Qdrant
│   └── retriever.py         # query_points + asymmetric embedding
│
├── guardrails/
│   ├── input_guardrails.py  # Topic, length, PII (rule-based)
│   ├── injection_guard.py   # Prompt injection (LLM-based)
│   ├── factuality_guard.py  # RAG grounding check (LLM-based)
│   └── output_guardrails.py # Itinerary completeness (rule-based)
│
├── memory/
│   └── user_context.py      # Load/save user preferences
│
├── hitl/
│   ├── budget_check.py      # Budget exceeded warning
│   └── final_approval.py    # Itinerary auto-approval
│
└── tests/
    ├── test_guardrails.py   # Unit tests (no LLM needed)
    ├── test_rag_eval.py     # RAGAS faithfulness + relevancy
    └── test_e2e.py          # DeepEval tool correctness + bias
```

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/YOUR_USERNAME/travel-research-agency.git
cd travel-research-agency
python3.12 -m venv .venv && source .venv/bin/activate
uv pip install -r requirements.txt
```

### 2. Configure API keys

```bash
cp .env.example .env
# Fill in your keys
```

### 3. Start Qdrant and ingest RAG documents

```bash
docker run -d -p 6333:6333 qdrant/qdrant
python -m rag.ingest
```

### 4. Run the Chainlit UI

```bash
chainlit run chainlit_app.py -w
# Opens at http://localhost:8000
```

### 5. Or run the FastAPI server

```bash
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

### 6. Or run the CLI demo

```bash
python run.py
```

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Readiness check |
| POST | `/plan` | Sync trip planning |
| POST | `/stream` | SSE real-time streaming |
| POST | `/resume` | Resume from HITL interrupt |
| GET | `/status/{thread_id}` | Poll trip status |

```bash
curl -X POST http://localhost:8000/plan \
  -H "Content-Type: application/json" \
  -d '{"query": "Plan a 7-day trip to Tokyo", "budget": 3000}'
```

## Graph Flow

```
START → load_user_prefs → input_guard → injection_guard → SUPERVISOR
                                                            │
              ┌─────────────────────────────────────────────┤
              ▼                  ▼                          ▼
          researcher        experience              safety_analyst
              │                  │                          │
              └── supervisor ────┘                  factuality_guard
                                                     (retry max 2)
                      │                                     │
                      ▼                                     │
              budget_optimizer ◄─────────────────────── supervisor
                      │
              budget_check
                      │
                   writer
                      │
              final_approval
                      │
               output_guard
                      │
              save_preferences → END
```

Three routing mechanisms:

1. **Fixed edges** — deterministic: `researcher → supervisor`
2. **Conditional edges** — state-based: guardrail pass/block, budget check
3. **Command routing** — dynamic: supervisor picks the next agent at runtime

## 4-Layer Guardrails

| Layer | Type | What It Checks |
|---|---|---|
| Input Guard | Rule-based | Topic relevance, length, PII detection |
| Injection Guard | LLM-based | Prompt injection attempts |
| Factuality Guard | LLM-based | Safety claims grounded in RAG context |
| Output Guard | Rule-based | Required itinerary sections exist |

## Evaluation

```bash
# Unit tests (no LLM needed)
pytest tests/test_guardrails.py -v

# RAG evaluation
pytest tests/test_rag_eval.py -v

# End-to-end evaluation
deepeval test run tests/test_e2e.py
```

| Metric | Framework | What It Measures |
|---|---|---|
| Faithfulness | RAGAS | Claims grounded in retrieved context |
| Response Relevancy | RAGAS | Answer addresses what was asked |
| Context Precision | RAGAS | Relevant chunks ranked at top |
| Itinerary Completeness | DeepEval GEval | All required sections present |
| Tool Correctness | DeepEval | Agents called the right tools |
| Hallucination | DeepEval | Output doesn't contradict context |

## Docker

```bash
docker compose up -d
# Starts: FastAPI app + Postgres + Qdrant
```

## Design Decisions

**Why multi-provider?** Each model is matched to its strength. Groq for speed (routing, search), Llama 4 for newer capabilities (experience, safety), HuggingFace for zero-cost budget analysis, Claude for prose quality (final itinerary).

**Why MCP over direct tool binding?** Decouples tools from agents. N agents × 1 protocol instead of N × M integrations. Tools can be tested independently and swapped without touching agent code.

**Why asymmetric embedding?** Jina v3 uses `task="retrieval.passage"` for documents and `task="retrieval.query"` for queries. This outperforms symmetric embedding because queries and documents have different linguistic patterns.

**Why 4-layer guardrails?** Rule-based guards run first (fast, free) to catch obvious issues. LLM-based guards handle nuanced threats. The factuality guard creates a retry loop — if the Safety Analyst hallucinates, it re-runs with stricter grounding (max 2 retries).

## Tech Stack

| Layer | Technology |
|---|---|
| Orchestration | LangGraph 1.0+ |
| Models | Groq, Llama 4, HuggingFace, Claude |
| Tools | FastMCP (Model Context Protocol) |
| RAG | Qdrant + Jina v3 embeddings |
| Guardrails | Rule-based + LLM-based (4 layers) |
| API | FastAPI + SSE streaming |
| UI | Chainlit |
| Evaluation | RAGAS + DeepEval |
| Observability | LangSmith |
| Deployment | Docker + Kubernetes |

## License

MIT
