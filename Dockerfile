# syntax=docker/dockerfile:1

FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app/src \
    PDM_USE_VENV=1 \
    PDM_VENV_IN_PROJECT=1 \
    PATH=/app/.venv/bin:$PATH

WORKDIR /app

RUN apt-get update \
    && apt-get install --no-install-recommends -y build-essential libpq-dev libffi-dev curl \
    && rm -rf /var/lib/apt/lists/*

ARG PDM_VERSION=2.25.9
RUN pip install --upgrade pip \
    && pip install "pdm==${PDM_VERSION}"

COPY pyproject.toml pdm.lock ./
RUN pdm install --prod --no-editable --no-self --frozen

COPY src ./src
COPY management ./management
COPY migrations ./migrations
COPY alembic.ini ./alembic.ini
COPY scripts ./scripts

EXPOSE 8000

CMD ["/app/scripts/start.sh"]
