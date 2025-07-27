from typing import List, Optional, Union

from fastapi import APIRouter, Depends, Body, Response, status
from fastapi.params import Query
from qdrant_client import AsyncQdrantClient
from sentence_transformers import SentenceTransformer

from deps import get_embedding_model
from qdrant_service.base import get_qdrant_client
from qdrant_service.service import QdrantService
from qdrant_service.types import QuestionLimit, QuestionAnswer, QASearchResult
from schemas import QADetailsSchema, QASchemaWithForceSave
from celery_app.tasks import daily_task
pattern_router = APIRouter()

@pattern_router.post("", response_model=QADetailsSchema)
async def add_new_pattern(
    data: QASchemaWithForceSave = Body(...),
    client: AsyncQdrantClient = Depends(get_qdrant_client),
    model: SentenceTransformer = Depends(get_embedding_model),
    response: Response = None
) -> QADetailsSchema:
    service = QdrantService(client, model)
    result = await service.search_similar_questions(QuestionLimit(question=data.question))

    if result and not data.force_save and result[0].score > 0.68:
        hit = result[0]
        response.status_code = status.HTTP_400_BAD_REQUEST
        return QADetailsSchema(
            question=hit.question,
            answer=hit.question,
            details="exists"
        )

    await service.save_question_answer_pattern(QuestionAnswer(question=data.question, answer=data.answer))
    response.status_code = status.HTTP_200_OK
    return QADetailsSchema(
        question=data.question,
        answer=data.answer,
        details="saved"
    )

@pattern_router.get("", response_model=List[QASearchResult])
async def get_answer_by_question(
    client: AsyncQdrantClient = Depends(get_qdrant_client),
    model: SentenceTransformer = Depends(get_embedding_model),
    question: str = Query(...),
) -> List[QASearchResult]:
    service = QdrantService(client, model)
    return await service.search_similar_questions(QuestionLimit(question=question))

@pattern_router.delete("")
async def delete_pattern(
    client: AsyncQdrantClient = Depends(get_qdrant_client),
    model: SentenceTransformer = Depends(get_embedding_model),
    uuid: str = Query(...),
):
    service = QdrantService(client, model)
    await service.delete_pattern_by_id(point_id=uuid)
    return {'details': 'deleted'}

@pattern_router.post("/start-task")
async def start_task():
    daily_task.delay()
    return {'details': 'started'}

@pattern_router.get("/get-all-texts")
async def get_all_texts(
    limit: int = Query(10, gt=0, le=100),
    cursor: Optional[Union[int, str]] = Query(None),
    client: AsyncQdrantClient = Depends(get_qdrant_client),
    model: SentenceTransformer = Depends(get_embedding_model),
):
    service = QdrantService(client, model)
    return await service.get_all_texts(limit=limit, cursor=cursor)

