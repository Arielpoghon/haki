# Haki — production-style container. Runs WITHOUT any chain keys: the API
# serves the dashboard, audit view and simulated attestations; live attesting
# stays local-only (chain/.env is never baked into an image).
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY api/ api/
COPY rules/ rules/
COPY data/ data/
COPY static/ static/
COPY conftest.py demo.sh ./

# audit trail must be writable in-container; mount a volume to persist it
RUN mkdir -p audit

ENV PORT=8000
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"

CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${PORT}"]
