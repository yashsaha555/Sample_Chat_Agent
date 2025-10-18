# Backend - IoT Diagnostics Agent

FastAPI service providing endpoints for uploading logs, chatting with a LangChain RAG agent, generating synthetic datasets, and sample logs.

## Endpoints

- POST /api/upload: multipart file upload (text files). Returns parsed items.
- POST /api/chat: { message: string, context?: string[] } -> { reply: string }
- POST /api/generate-dataset: Build and ingest synthetic dataset into Chroma.
- POST /api/generate-sample-logs?count=5: Produce example txt logs for testing.
- GET /api/health: Healthcheck.

## Environment

Copy `.env.example` to `.env` and set keys.

- OPENROUTER_API_KEY
- OPENROUTER_BASE_URL (default https://openrouter.ai/api/v1)
- OPENROUTER_MODEL (default openai/gpt-4o)
- VECTOR_DB_PATH (default ./storage/chroma)
- EMBEDDING_MODEL (default sentence-transformers/all-MiniLM-L6-v2)

## Run

1. Create venv and install requirements
2. Start server

```bash
python -m venv .venv
source .venv/Scripts/activate
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Notes

- Guardrails applied at upload, query, retrieval, and generation stages.
- Uses OpenRouter for LLM and HuggingFace embeddings for local vector search via Chroma.
