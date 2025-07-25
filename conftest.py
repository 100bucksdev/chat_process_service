import pytest_asyncio
from typing import AsyncGenerator
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock

from deps import get_embedding_model
from main import create_app
from qdrant_service.base import get_qdrant_client


class DummyVector(list):
    def tolist(self):
        return list(self)

class DummyModel:
    def __init__(self, dim: int = 3):
        self.dim = dim

    def encode(self, text, convert_to_numpy=True):
        return DummyVector([0.1] * self.dim)

    def get_sentence_embedding_dimension(self):
        return self.dim


@pytest_asyncio.fixture
async def app() -> FastAPI:
    return create_app()


@pytest_asyncio.fixture
async def qdrant_mock() -> AsyncMock:
    client = AsyncMock()
    client.get_collection.return_value = None
    client.create_collection.return_value = None
    client.upsert.return_value = None
    client.delete.return_value = None
    client.scroll.return_value = ([], None)
    return client


@pytest_asyncio.fixture
async def embedding_model() -> DummyModel:
    return DummyModel(dim=3)


@pytest_asyncio.fixture
async def client(
    app: FastAPI, qdrant_mock: AsyncMock, embedding_model: DummyModel
) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_qdrant_client():
        yield qdrant_mock

    def override_get_embedding_model():
        return embedding_model

    app.dependency_overrides[get_qdrant_client] = override_get_qdrant_client
    app.dependency_overrides[get_embedding_model] = override_get_embedding_model

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
