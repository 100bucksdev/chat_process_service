from typing import AsyncGenerator
from qdrant_client import AsyncQdrantClient
import os

from sentence_transformers import SentenceTransformer


async def get_qdrant_client() -> AsyncGenerator[AsyncQdrantClient, None]:
    client = AsyncQdrantClient(url=os.getenv("QDRANT_URL", "http://127.0.0.1:6333"))
    try:
        yield client
    finally:
        await client.close()

def get_model() -> SentenceTransformer:
    return SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")