FROM python:3.12-slim AS base
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
ENV UV_PROJECT_ENVIRONMENT="/opt/venv"
WORKDIR /app
COPY pyproject.toml uv.lock* ./

FROM base AS prod
RUN uv sync --frozen --no-dev
COPY . .
EXPOSE 8000
CMD ["uv", "run", "uvicorn", "src.core.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

FROM base AS dev
RUN uv sync --frozen          
COPY . .
EXPOSE 8000
CMD ["uv", "run", "uvicorn", "src.core.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]