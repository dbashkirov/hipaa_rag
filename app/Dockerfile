FROM python:3.12-slim

# 1) Poetry
RUN pip install --no-cache-dir poetry

WORKDIR /code
COPY pyproject.toml poetry.lock* ./
RUN poetry config virtualenvs.create false \
 && poetry install --no-interaction --no-ansi --no-root

# 2) код
COPY . .
