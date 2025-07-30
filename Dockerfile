# Базовый образ
FROM python:3.13-slim

ENV POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Системные зависимости + pg_config из libpq-dev
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
  && rm -rf /var/lib/apt/lists/*

# Poetry
RUN pip install --no-cache-dir poetry

WORKDIR /app

# Кэшируем зависимости
COPY pyproject.toml poetry.lock* /app/
RUN poetry install --no-root

# Копируем исходники
COPY . /app

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
