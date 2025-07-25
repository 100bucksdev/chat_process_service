import asyncio

from celery import signals
from qdrant_client import AsyncQdrantClient
from sentence_transformers import SentenceTransformer
from telebot import TeleBot
from celery_app import celery_app
from celery_app.proccess_chat import process_messages_from_chat, save_q_a_patterns, process_chats
from config import QDRANT_URL, TELEGRAM_BOT_TOKEN, ADMIN_TG_ID
from qdrant_service.base import get_model

MODEL: SentenceTransformer | None = None
bot = TeleBot(TELEGRAM_BOT_TOKEN)

@signals.worker_process_init.connect
def preload_resources(**kwargs):
    global MODEL
    MODEL = get_model()

@celery_app.task(max_retries=0)
def process_chat(chat_id: int):
    asyncio.run(process_messages_from_chat(chat_id))

@celery_app.task()
def daily_task():
    asyncio.run(process_chats())

@celery_app.task(max_retries=0)
def save_pattern(question: str, answer: str):
    client = AsyncQdrantClient(url=QDRANT_URL)
    asyncio.run(save_q_a_patterns(question, answer, client, MODEL))

@celery_app.task()
def send_notification(text: str):
    bot.send_message(chat_id=ADMIN_TG_ID, text=text, parse_mode='HTML')






