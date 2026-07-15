FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN addgroup --system app && adduser --system --ingroup app app

COPY --chown=app:app pyproject.toml README.md ./
COPY --chown=app:app src ./src
RUN python -m pip install --upgrade "pip>=26.1.2" && pip install --no-cache-dir . && pip check

RUN mkdir -p /app/data && chown -R app:app /app && python -m compileall -q /app/src
USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/readyz', timeout=2)"

CMD ["uvicorn", "nyxora_concierge.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-server-header", "--no-access-log", "--limit-concurrency", "100", "--timeout-keep-alive", "5"]

