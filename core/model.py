from typing import Optional
from sentence_transformers import SentenceTransformer
from qdrant_service.base import get_model

_model: Optional[SentenceTransformer] = None

def load_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = get_model()
    return _model
