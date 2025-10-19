# Contextual Assistant - Full Stack

This project provides a Next.js frontend and a Python FastAPI backend for a grounded RAG chatbot. It embeds the any document into a persistent Chroma vector DB using FastEmbed, retrieves relevant chunks, and answers via OpenRouter. Guardrails keep answers within provided context and avoid hallucinations.

Features:

- Next.js frontend (TypeScript) chat UI with file upload
- FastAPI backend with Chroma + FastEmbed embeddings
- OpenRouter LLM integration
- Guardrails: context-only, retrieval gating, refusal on insufficient context

## Structure

```
.
├── frontend/                  # Next.js app (App Router, Tailwind)
│   ├── app/
│   │   ├── page.tsx          # Chat UI calling backend endpoints
│   │   └── api-helpers.ts    # API base + helpers
│   ├── components/
│   ├── package.json
│   └── ...
├── backend/
│   ├── main.py               # FastAPI app + Chroma + FastEmbed + OpenRouter
│   ├── requirements.txt
│   └── chroma_db/            # created at runtime
```

## Problem Statement Coverage

1. Embed a file into a Chroma vector DB for context
2. RAG chat using retrieved context plus any uploaded file text
3. Concise, user-friendly answers with guardrails
4. Refusal for out-of-scope or insufficient context

## Setup & Run

Backend (Windows PowerShell):

```powershell
# From repo root
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt

# Ensure backend/.env has OPENROUTER_API_KEY set
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

Backend (Git Bash):

```bash
# From repo root
python -m venv .venv
source .venv/Scripts/activate
pip install -r backend/requirements.txt

uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

## Backend environment

- Copy `backend/.env.example` to `backend/.env` and set:
  - `OPENROUTER_API_KEY` (required)
  - Optional Windows cache helpers on first run:
    - `FASTEMBED_CACHE_PATH=./backend/.cache/fastembed`
    - `HF_HUB_DISABLE_SYMLINKS=1`

## Using a different document

- The bundled `Atomic habits ( PDFDrive ).pdf` is just an example. You can use any PDF/text file.
- Place your file at the repo root (same level as `frontend/` and `backend/`). Then either:
  - Rename your file to `Atomic habits ( PDFDrive ).pdf` to match the default path, or
  - Edit `PDF_PATH` in `backend/main.py` to point to your file name, for example:

```python
# backend/main.py
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
PDF_PATH = os.path.join(PROJECT_ROOT, "MyDoc.pdf")
```

- Restart the backend and click "Build Dataset" in the UI to re-ingest your document.
- You can also attach files in the chat UI; their extracted text is added as per-message context.

## Frontend

- Copy `frontend/.env.local.example` to `frontend/.env.local` and set `NEXT_PUBLIC_API_URL=http://localhost:8000`
- Install and run dev server:

```bash
npm ci --prefix frontend
npm run dev --prefix frontend
```

```bash
# From repo root
cd "frontend"
npm ci
npm run dev
```

The app will start at http://localhost:3000 and expects the backend at http://localhost:8000.

## Usage

1. Click "Build Dataset" in the UI, or call `POST /api/generate-dataset` to embed the PDF into Chroma.
2. Type your message or upload files; click Send. Responses are grounded to retrieved/uploaded context.

Useful endpoints:

- `GET /health` — server check
- `GET /api/status` — diagnostics: PDF found, OpenRouter configured, collection exists, doc count
- `POST /api/generate-dataset`
- `POST /api/upload`
- `POST /api/chat`

## Environment variables (backend)

- `OPENROUTER_API_KEY` (required)
- `OPENROUTER_MODEL` (required)
- `FASTEMBED_CACHE_PATH` (optional; set a local cache path on Windows)
- `HF_HUB_DISABLE_SYMLINKS=1` (optional; reduces Windows symlink warnings)

- Keep your OpenRouter API key only in `.env` files. Never commit secrets.
