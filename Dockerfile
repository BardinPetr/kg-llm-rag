FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends gcc g++ libc-dev libffi-dev && rm -rf /var/lib/apt/lists/*

WORKDIR /app

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV UV_LINK_MODE=copy

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

RUN apt-get update && apt-get install -y graphviz
RUN apt-get install -y pkg-config libcairo2-dev

RUN groupadd -g 1000 main && useradd -m -u 1000 -g main main
RUN chown main:main /app
USER main
WORKDIR /app

COPY pyproject.toml uv.lock README.md ./

RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --no-install-project
#RUN --mount=type=bind,src=/home/petr/.cache/uv,dst=/root/.cache/uv uv sync --frozen --no-install-project

COPY src/ ./

RUN uv sync --frozen

#CMD ["uv", "run", "celery", "-A", "your_app.celery", "worker", "--loglevel=info", "--pool=gevent", "--concurrency=10"]
