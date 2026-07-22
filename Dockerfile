# BC Legal AI Associate — API + static client
# Non-root, no secrets. Not for public client-file hosting without MFA/ACL.
FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_MODE=development \
    PYTHONPATH=/app

WORKDIR /app

RUN useradd --create-home --uid 10001 appuser

COPY pyproject.toml README.md ./
COPY architecture ./architecture
COPY backend ./backend
COPY services ./services
COPY knowledgebase ./knowledgebase
COPY middleware ./middleware
COPY frontend ./frontend
COPY templates ./templates
COPY agents ./agents
COPY legal_knowledge ./legal_knowledge
COPY config ./config

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir "fastapi>=0.115" "uvicorn[standard]>=0.30" "pydantic>=2" "httpx>=0.27" \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"

CMD ["uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
