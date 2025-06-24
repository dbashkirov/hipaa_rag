FROM python:3.12-slim

RUN pip install --no-cache-dir poetry

WORKDIR /ui
COPY pyproject.toml poetry.lock* ./
RUN poetry config virtualenvs.create false \
 && poetry install --no-interaction --no-ansi --no-root
COPY . .
