FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app
COPY apps/api/pyproject.toml apps/api/uv.lock ./
RUN uv sync --frozen --no-dev
COPY apps/api/alembic.ini ./
COPY apps/api/alembic ./alembic
COPY apps/api/src ./src
COPY apps/api/deploy.py ./

ENV PATH="/app/.venv/bin:$PATH" PYTHONPATH=/app/src
EXPOSE 8000
CMD ["python", "deploy.py"]
