import pytest
from fastapi import status
from types import SimpleNamespace


def _make_point(point_id: str, score: float, question: str, answer: str):
    return SimpleNamespace(id=point_id, score=score, payload={"question": question, "answer": answer})


@pytest.mark.asyncio
async def test_add_new_pattern_saved_when_not_exists(client, qdrant_mock):
    qdrant_mock.query_points.return_value = SimpleNamespace(points=[])
    payload = {"question": "q1", "answer": "a1", "force_save": False}
    resp = await client.post("/pattern", json=payload)
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["details"] == "saved"
    assert data["question"] == "q1"
    assert data["answer"] == "a1"
    assert qdrant_mock.upsert.called


@pytest.mark.asyncio
async def test_add_new_pattern_returns_400_if_similar_exists_and_not_forced(client, qdrant_mock):
    hit = _make_point("1", 0.9, "existing_q", "existing_a")
    qdrant_mock.query_points.return_value = SimpleNamespace(points=[hit])
    payload = {"question": "q1", "answer": "a1", "force_save": False}
    resp = await client.post("/pattern", json=payload)
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    data = resp.json()
    assert data["details"] == "exists"
    assert data["question"] == "existing_q"
    assert qdrant_mock.upsert.call_count == 0


@pytest.mark.asyncio
async def test_add_new_pattern_forced_saves_even_if_similar_exists(client, qdrant_mock):
    hit = _make_point("1", 0.9, "existing_q", "existing_a")
    qdrant_mock.query_points.return_value = SimpleNamespace(points=[hit])
    payload = {"question": "q1", "answer": "a1", "force_save": True}
    resp = await client.post("/pattern", json=payload)
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["details"] == "saved"
    assert data["question"] == "q1"
    assert qdrant_mock.upsert.called


@pytest.mark.asyncio
async def test_get_answer_by_question_returns_results(client, qdrant_mock):
    hit1 = _make_point("1", 0.8, "q1", "a1")
    hit2 = _make_point("2", 0.7, "q2", "a2")
    qdrant_mock.query_points.return_value = SimpleNamespace(points=[hit1, hit2])
    resp = await client.get("/pattern", params={"question": "some"})
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["question"] == "q1"
    assert data[0]["answer"] == "a1"
    assert "score" in data[0]
    assert "uuid" in data[0]


@pytest.mark.asyncio
async def test_delete_pattern(client, qdrant_mock):
    resp = await client.delete("/pattern", params={"uuid": "abc"})
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json() == {"details": "deleted"}
    assert qdrant_mock.delete.called
    call = qdrant_mock.delete.call_args.kwargs
    assert "points_selector" in call
    assert call["points_selector"] == ["abc"]


def _make_point(point_id: str, score: float, question: str, answer: str):
    return SimpleNamespace(id=point_id, score=score, payload={"question": question, "answer": answer})

@pytest.mark.asyncio
async def test_add_new_pattern_borderline_threshold_saves(client, qdrant_mock):
    hit = _make_point("1", 0.68, "existing_q", "existing_a")
    qdrant_mock.query_points.return_value = SimpleNamespace(points=[hit])
    payload = {"question": "q1", "answer": "a1", "force_save": False}
    resp = await client.post("/pattern", json=payload)
    assert resp.status_code == status.HTTP_200_OK
    data = resp.json()
    assert data["details"] == "saved"
    assert qdrant_mock.upsert.called

@pytest.mark.asyncio
async def test_add_new_pattern_without_force_save_field_defaults_to_false(client, qdrant_mock):
    hit = _make_point("1", 0.9, "existing_q", "existing_a")
    qdrant_mock.query_points.return_value = SimpleNamespace(points=[hit])
    payload = {"question": "q1", "answer": "a1"}
    resp = await client.post("/pattern", json=payload)
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    data = resp.json()
    assert data["details"] == "exists"
    assert qdrant_mock.upsert.call_count == 0

@pytest.mark.asyncio
async def test_get_answer_by_question_returns_empty_list(client, qdrant_mock):
    qdrant_mock.query_points.return_value = SimpleNamespace(points=[])
    resp = await client.get("/pattern", params={"question": "some"})
    assert resp.status_code == status.HTTP_200_OK
    assert resp.json() == []

@pytest.mark.asyncio
async def test_post_validation_error_on_missing_question(client):
    payload = {"answer": "a1", "force_save": False}
    resp = await client.post("/pattern", json=payload)
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

@pytest.mark.asyncio
async def test_get_validation_error_on_missing_question_param(client):
    resp = await client.get("/pattern")
    assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

@pytest.mark.asyncio
async def test_delete_pattern_raises_when_service_crashes(client, qdrant_mock):
    qdrant_mock.delete.side_effect = RuntimeError("boom")
    with pytest.raises(RuntimeError):
        await client.delete("/pattern", params={"uuid": "abc"})