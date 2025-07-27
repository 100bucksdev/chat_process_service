from typing import List, Dict

from qdrant_client import AsyncQdrantClient
from sentence_transformers import SentenceTransformer

from config import CHAT_BOT_SERVICE_URL
from external_service import make_request
from qdrant_service.service import QdrantService
from qdrant_service.types import QuestionLimit, QuestionAnswer

CHUNK_SIZE = 3000


async def process_chats():
    from celery_app.tasks import process_chat, send_notification
    chat_list = await make_request('data-for-processing/get-chats-ids')
    if chat_list['status'] != 200:
        send_notification.delay(f"<b>process_chats</b>: ❌ status={chat_list['status']}")
        return
    ids = chat_list.get('body') or []
    if not ids:
        send_notification.delay("<b>process_chats</b>: 💤 <i>Нет чатов для обработки</i>")
        return
    for chat_id in ids:
        process_chat.delay(chat_id)
    send_notification.delay(f"<b>process_chats</b>: 🚀 Запущено задач: <b>{len(ids)}</b>")


async def process_messages_from_chat(chat_id: int):
    from celery_app.tasks import save_pattern, send_notification
    send_notification.delay(f"<b>chat {chat_id}</b>: 🔎 Старт обработки")
    messages = await make_request(f'message/{chat_id}/get-unprocessed-messages')
    if messages['status'] != 200:
        send_notification.delay(f"<b>chat {chat_id}</b>: ❌ status={messages['status']}")
        return
    body = messages.get('body') or []
    total_messages = len(body)
    chunks = build_chunks(body, CHUNK_SIZE)
    total_chunks = len(chunks)
    total_patterns = 0
    for i, chunk in enumerate(chunks, 1):
        text = messages_to_text(chunk)
        response = await process_using_ai(text)
        if response:
            for pattern in response:
                save_pattern.delay(pattern['question'], pattern['answer'])
                total_patterns += 1
        send_notification.delay(f"<b>chat {chat_id}</b>: 🧩 Чанк {i}/{total_chunks} обработан")
    await make_request(f'message/{chat_id}/mark-as-processed', method='POST')
    send_notification.delay(f"<b>chat {chat_id}</b>: ✅ Сообщений: <b>{total_messages}</b>, чанков: <b>{total_chunks}</b>, сохранённых паттернов: <b>{total_patterns}</b>")


def build_chunks(messages: List[Dict], chunk_size: int) -> List[List[Dict]]:
    chunks: List[List[Dict]] = []
    current: List[Dict] = []
    current_len = 0
    for msg in messages:
        seg = f'{msg["sender"]}: {msg["message_text"]}\n'
        current.append(msg)
        current_len += len(seg)
        if current_len >= chunk_size and msg["sender"].lower() == "staff":
            chunks.append(current)
            current = []
            current_len = 0
    if current:
        if current[-1]["sender"].lower() == "staff":
            chunks.append(current)
        else:
            last_staff_index = -1
            for idx in range(len(current) - 1, -1, -1):
                if current[idx]["sender"].lower() == "staff":
                    last_staff_index = idx
                    break
            if last_staff_index != -1:
                chunks.append(current[:last_staff_index + 1])
                remaining = current[last_staff_index + 1:]
                if remaining:
                    if remaining[-1]["sender"].lower() == "staff":
                        chunks.append(remaining)
                    else:
                        for msg in messages[messages.index(remaining[-1]) + 1:]:
                            remaining.append(msg)
                            if msg["sender"].lower() == "staff":
                                break
                        chunks.append(remaining)
            else:
                for msg in messages[messages.index(current[0]):]:
                    current.append(msg)
                    if msg["sender"].lower() == "staff":
                        break
                chunks.append(current)
    return chunks


def messages_to_text(messages: List[Dict]) -> str:
    return ''.join(f'{m["sender"]}: {m["message_text"]}\n' for m in messages)


async def process_using_ai(text: str):
    from celery_app.tasks import send_notification
    response = await make_request(base_url=CHAT_BOT_SERVICE_URL, method='POST', url='process-questions', data={'text': text})
    if response['status'] == 200:
        data = response['body'].get('items')
        size = len(data) if data else 0
        send_notification.delay(f"<b>AI</b>: 🧠 Найдено Q/A: <b>{size}</b>")
        return data
    send_notification.delay(f"<b>AI</b>: ❌ status={response['status']}")
    return None


async def save_q_a_patterns(question: str, answer: str, client: AsyncQdrantClient, model: SentenceTransformer):
    from celery_app.tasks import send_notification
    service = QdrantService(client, model)
    response = await service.search_similar_questions(QuestionLimit(question=question))
    top_result = None
    if response:
        top_result = response[0]
        if top_result.score >= 0.68:
            send_notification.delay(f"<b>Qdrant</b>: ⏭️ Пропущено (score={top_result.score:.2f} ≥ 0.68)")
            return
    await service.save_question_answer_pattern(QuestionAnswer(question=question, answer=answer))
    send_notification.delay(f"<b>Qdrant</b>: 💾 Сохранено (score={f'{top_result.score:.2f}' if top_result else '?' })")
