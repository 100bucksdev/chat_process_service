from fastapi import Request
from sentence_transformers import SentenceTransformer

def get_embedding_model(request: Request) -> SentenceTransformer:
    return request.app.state.model
