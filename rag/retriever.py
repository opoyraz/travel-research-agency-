"""
Travel Research Agency — RAG Retriever
Embeds queries with Jina v3, searches Qdrant, returns grounded context.
Used by Safety Analyst agent to ground responses in real advisory data.
"""

import os
import requests
from dotenv import load_dotenv
from qdrant_client import QdrantClient, models
from langchain_core.tools import tool

load_dotenv()

# ═══════════════════════════════════════════════
#  CONFIG
# ═══════════════════════════════════════════════

JINA_API_KEY = os.getenv("JINA_API_KEY")
JINA_URL = "https://api.jina.ai/v1/embeddings"
EMBED_MODEL = "jina-embeddings-v3"
EMBED_DIM = 1024

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION = "travel_advisories"


# ═══════════════════════════════════════════════
#  QUERY EMBEDDING
# ═══════════════════════════════════════════════

def embed_query(text: str) -> list[float]:
    """Embed a single query using Jina AI (query-specific task)."""
    response = requests.post(
        JINA_URL,
        headers={
            "Authorization": f"Bearer {JINA_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": EMBED_MODEL,
            "input": [text],
            "task": "retrieval.query",    # query-specific optimization
            "dimensions": EMBED_DIM,
        },
    )
    response.raise_for_status()
    return response.json()["data"][0]["embedding"]


# ═══════════════════════════════════════════════
#  QDRANT RETRIEVAL
# ═══════════════════════════════════════════════

def retrieve_advisories(
    query: str,
    country_code: str = None,
    top_k: int = 3,
) -> list[dict]:
    """Retrieve relevant travel advisories from Qdrant.

    Args:
        query: User's safety question
        country_code: Optional 2-letter filter (e.g., "JP" for Japan)
        top_k: Number of results to return
    """
    client = QdrantClient(url=QDRANT_URL)
    query_vector = embed_query(query)

    # Build optional metadata filter
    query_filter = None
    if country_code:
        query_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="code",
                    match=models.MatchValue(value=country_code),
                )
            ]
        )

    # Search using query_points() — current Qdrant API
    results = client.query_points(
        collection_name=COLLECTION,
        query=query_vector,
        query_filter=query_filter,
        limit=top_k,
        with_payload=True,
    ).points

    return [
        {
            "text": hit.payload["text"],
            "country": hit.payload.get("country", "Unknown"),
            "advisory_level": hit.payload.get("advisory_level", 0),
            "title": hit.payload.get("title", ""),
            "last_updated": hit.payload.get("last_updated", ""),
            "score": hit.score,
        }
        for hit in results
    ]


# ═══════════════════════════════════════════════
#  LANGCHAIN TOOL WRAPPER (for Safety Analyst)
# ═══════════════════════════════════════════════

@tool
def rag_travel_advisory(query: str, country_code: str = "") -> str:
    """Search travel advisories and safety information for a country.

    Args:
        query: Safety-related question about the destination
        country_code: Two-letter country code (e.g., "JP", "FR", "BR")
    """
    results = retrieve_advisories(
        query=query,
        country_code=country_code if country_code else None,
        top_k=3,
    )

    if not results:
        return "No travel advisories found for this destination."

    # Format retrieved docs for the agent
    formatted = []
    for i, doc in enumerate(results, 1):
        formatted.append(
            f"[Source {i}] {doc['country']} — {doc['title']} "
            f"(Level {doc['advisory_level']}, Updated: {doc['last_updated']})\n"
            f"{doc['text']}\n"
            f"Relevance: {doc['score']:.3f}"
        )

    return "\n\n".join(formatted)
