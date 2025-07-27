from typing import List, Optional, Union, Dict
from uuid import uuid4
from qdrant_client.http.models import Distance, VectorParams, PointStruct

from qdrant_client import AsyncQdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
from sentence_transformers import SentenceTransformer

from qdrant_service.types import QuestionAnswer, QuestionLimit, QASearchResult


class QdrantService:
    COLLECTION_NAME = "user_questions"

    def __init__(self, client: AsyncQdrantClient, model: SentenceTransformer):
        self.client = client
        self.model = model
        self._collection_ready = False

    async def _ensure_collection(self):
        if self._collection_ready:
            return
        try:
            await self.client.get_collection(collection_name=self.COLLECTION_NAME)
        except UnexpectedResponse as e:
            if e.status_code == 404:
                await self.client.create_collection(
                    self.COLLECTION_NAME,
                    vectors_config=VectorParams(
                        size=self.model.get_sentence_embedding_dimension(),
                        distance=Distance.COSINE
                    )
                )
            else:
                raise
        self._collection_ready = True

    async def save_question_answer_pattern(self, data: QuestionAnswer):
        print('processing and saving text: ', data.question, '->', data.answer, '...')
        await self._ensure_collection()
        vector = self.model.encode(data.question, convert_to_numpy=True).tolist()
        await self.client.upsert(
            collection_name=self.COLLECTION_NAME,
            points=[
                PointStruct(
                    id=str(uuid4()),
                    vector=vector,
                    payload={"question": data.question, "answer": data.answer}
                )
            ]
        )

    async def delete_pattern_by_id(self, point_id: str):
        await self._ensure_collection()
        await self.client.delete(collection_name=self.COLLECTION_NAME, points_selector=[point_id])


    async def search_similar_questions(self, data: QuestionLimit)-> List[QASearchResult]:
        await self._ensure_collection()
        query_vector = self.model.encode(data.question, convert_to_numpy=True).tolist()
        results = await self.client.query_points(
            collection_name=self.COLLECTION_NAME,
            query=query_vector,
            limit=data.limit,
            with_payload=True
        )
        return [
            QASearchResult(
                question=p.payload.get("question"),
                answer=p.payload.get("answer"),
                score=p.score,
                uuid=p.id
            )
        for p in results.points
    ]

    async def get_all_texts(self, limit: int, cursor: Optional[Union[int, str]]) -> Dict[str, object]:
        await self._ensure_collection()
        points, next_cursor = await self.client.scroll(
            collection_name=self.COLLECTION_NAME,
            limit=limit,
            offset=cursor,
            with_payload=True,
            with_vectors=False
        )
        items: List[Dict[str, object]] = [
            {"id": p.id, "question": p.payload.get("question"), "answer": p.payload.get("answer")}
            for p in points
        ]
        return {"items": items, "next": next_cursor}