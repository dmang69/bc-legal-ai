# BC Legal AI Associate — API (production-oriented image)
# Non-root, no secrets baked in. Build: docker build -t bc-legal-ai:1.0.0 .
FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_MODE=production \
    PYTHONPATH=/app \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /app/data \
    && chown -R appuser:appuser /app

# Dependency metadata first (better layer cache)
COPY pyproject.toml README.md requirements.txt ./
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
COPY skills ./skills
COPY legislation ./legislation
COPY lexicon ./lexicon
COPY model ./model
COPY schema ./schema
COPY evaluations ./evaluations
COPY fixtures ./fixtures
COPY scripts ./scripts

# Runtime deps: API + Postgres + PDF/DOCX export (OCR optional at deploy time)
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir \
        "fastapi>=0.115.0" \
        "uvicorn[standard]>=0.30.0" \
        "pydantic>=2.0" \
        "httpx>=0.27.0" \
        "pyyaml>=6.0" \
        "pypdf>=4.0" \
        "python-docx>=1.1.0" \
        "psycopg[binary]>=3.1" \
        "psycopg_pool>=3.2" \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/live', timeout=4)"

# Single worker by default; set --workers only with ALA_POSTGRES_URL
CMD ["uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
