import os

from dotenv import load_dotenv


load_dotenv()

DEBUG = os.getenv("DEBUG", "true").lower() == "true"

APP_ID=os.getenv('APP_ID')
APP_HASH=os.getenv('APP_HASH')

DB_HOST = os.getenv("BOT_DB_HOST")
DB_PORT = os.getenv("BOT_DB_PORT")
DB_USER = os.getenv("BOT_DB_USER")
DB_PASSWORD = os.getenv("BOT_DB_PASS")
DB_NAME = os.getenv("BOT_DB_NAME")

REDIS_URL=os.getenv("REDIS_URL")

TELEGRAM_BOT_TOKEN=os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_TG_ID=os.getenv("ADMIN_TG_ID")

CHATS_MANAGER_URL=os.getenv("CHATS_MANAGER_URL")
CHAT_BOT_SERVICE_URL=os.getenv("CHAT_BOT_SERVICE_URL")
QDRANT_URL=os.getenv("QDRANT_URL")