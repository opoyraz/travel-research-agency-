"""
Travel Research Agency — RAG Ingestion Pipeline
Chunks travel advisories, embeds with Jina v3, stores in Qdrant.
Run once to populate the vector database.

Usage:
    python -m rag.ingest
"""

import os
import requests
from dotenv import load_dotenv
from qdrant_client import QdrantClient, models
from langchain_text_splitters import RecursiveCharacterTextSplitter

from rag.documents import TRAVEL_ADVISORIES

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
#  EMBEDDING
# ═══════════════════════════════════════════════

def embed_texts(texts: list[str], task: str = "retrieval.passage") -> list[list[float]]:
    """Embed a batch of texts using Jina AI.

    Args:
        texts: List of text strings to embed
        task: "retrieval.passage" for documents, "retrieval.query" for queries
    """
    response = requests.post(
        JINA_URL,
        headers={
            "Authorization": f"Bearer {JINA_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": EMBED_MODEL,
            "input": texts,
            "task": task,
            "dimensions": EMBED_DIM,
        },
    )
    response.raise_for_status()
    return [item["embedding"] for item in response.json()["data"]]


# ═══════════════════════════════════════════════
#  CHUNKING
# ═══════════════════════════════════════════════

def chunk_documents() -> list[dict]:
    """Split advisory documents into chunks with metadata."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=400,         # ~100 tokens per chunk
        chunk_overlap=50,       # overlap to preserve context at boundaries
        separators=["\n\n", "\n", ". ", " "],
    )

    chunks = []
    for doc in TRAVEL_ADVISORIES:
        text_chunks = splitter.split_text(doc["content"])
        for i, chunk in enumerate(text_chunks):
            chunks.append({
                "text": chunk,
                "metadata": {
                    "country": doc["country"],
                    "code": doc["code"],
                    "advisory_level": doc["advisory_level"],
                    "title": doc["title"],
                    "last_updated": doc["last_updated"],
                    "chunk_index": i,
                },
            })

    return chunks


# ═══════════════════════════════════════════════
#  QDRANT STORAGE
# ═══════════════════════════════════════════════

def ingest():
    """Full ingestion pipeline: chunk → embed → store in Qdrant."""
    print("═══ Travel Advisory Ingestion Pipeline ═══")

    # 1. Chunk
    chunks = chunk_documents()
    print(f"✅ Chunked {len(TRAVEL_ADVISORIES)} documents → {len(chunks)} chunks")

    # 2. Embed
    texts = [c["text"] for c in chunks]
    embeddings = embed_texts(texts, task="retrieval.passage")
    print(f"✅ Embedded {len(embeddings)} chunks (dim={EMBED_DIM})")

    # 3. Connect to Qdrant
    client = QdrantClient(url=QDRANT_URL)

    # Recreate collection (idempotent)
    if client.collection_exists(COLLECTION):
        client.delete_collection(COLLECTION)

    client.create_collection(
        collection_name=COLLECTION,
        vectors_config=models.VectorParams(
            size=EMBED_DIM,
            distance=models.Distance.COSINE,
        ),
    )

    # 4. Upsert points
    points = [
        models.PointStruct(
            id=i,
            vector=embeddings[i],
            payload={
                "text": chunks[i]["text"],
                **chunks[i]["metadata"],
            },
        )
        for i in range(len(chunks))
    ]

    client.upsert(collection_name=COLLECTION, points=points)
    print(f"✅ Stored {len(points)} vectors in Qdrant collection '{COLLECTION}'")

    # Verify
    info = client.get_collection(COLLECTION)
    print(f"✅ Collection status: {info.status}, points: {info.points_count}")


if __name__ == "__main__":
    ingest()
