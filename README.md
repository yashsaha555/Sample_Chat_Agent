# Premium Chatbot (Next.js + FastAPI)

An ultra-premium chat experience similar to ChatGPT/DeepSeek with:

- Next.js frontend (TypeScript) with elegant, polished UI
- FastAPI backend (Python)
- File uploads: PDF, DOCX, PPTX, TXT, CSV, XLSX, Images (PNG/JPG)
- OCR for images and photos (Tesseract)
- Math OCR in images via optional Mathpix or Vision LLM
- Pluggable LLM providers: OpenAI, DeepSeek, Ollama (local), Azure OpenAI

## Folder structure

```
.
├── frontend/              # Next.js app (App Router, Tailwind)
│   ├── app/
│   ├── components/
│   ├── public/
│   ├── styles/
│   ├── next.config.mjs
│   ├── package.json
│   ├── postcss.config.mjs
│   ├── tailwind.config.ts
│   └── tsconfig.json
└── backend/               # FastAPI app
    ├── app/
    │   ├── main.py
    │   ├── models/
    │   │   └── schemas.py
    │   └── services/
    │       ├── doc_processing.py
    │       ├── llm_providers.py
    │       └── ocr.py
    └── requirements.txt
```

## Prerequisites

- Node.js 18+ and npm
- Python 3.10+
- Tesseract OCR installed (for image text). On Windows, download from: https://github.com/UB-Mannheim/tesseract/wiki
  - After install, set environment variable `TESSERACT_CMD` to the installed tesseract.exe path (e.g., `C:\\Program Files\\Tesseract-OCR\\tesseract.exe`).

Optional for best math OCR:

- Mathpix account (set `MATHPIX_APP_ID` and `MATHPIX_APP_KEY`)
- Or Vision LLM (OpenAI): set `OPENAI_API_KEY` and choose a vision model (e.g., `gpt-4o-mini`) via `VISION_MODEL`.

## Backend setup (FastAPI)

Create a Python venv, install deps, and run the server:

```bash
# From repo root
cd "backend"
python -m venv .venv
source .venv/bin/activate || source .venv/Scripts/activate
pip install -r requirements.txt

# Environment (choose one provider)
# OpenAI
export LLM_PROVIDER=openai
export OPENAI_API_KEY=your_key
export OPENAI_MODEL=gpt-4o-mini
# DeepSeek (OpenAI-compatible endpoint)
# export LLM_PROVIDER=deepseek
# export OPENAI_API_KEY=your_deepseek_key
# export OPENAI_BASE_URL=https://api.deepseek.com
# export OPENAI_MODEL=deepseek-chat
# Ollama (local)
# export LLM_PROVIDER=ollama
# export OLLAMA_MODEL=llama3.1:8b

# Optional: Math OCR
# export MATHPIX_APP_ID=...
# export MATHPIX_APP_KEY=...
# or Vision LLM
# export VISION_MODEL=gpt-4o-mini

# Tesseract (Windows example)
# export TESSERACT_CMD="C:\\Program Files\\Tesseract-OCR\\tesseract.exe"

# Run FastAPI
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Frontend setup (Next.js)

```bash
# From repo root
cd "frontend"
npm install
npm run dev
```

The app will start at http://localhost:3000 and expects the backend at http://localhost:8000.

## Usage

- Type a message and press Enter to chat with the LLM.
- Drag-and-drop or use the attach button to upload files. Extracted text is appended as context for the next chat call.
- Upload images containing text or math; if Mathpix or Vision model is configured, math expressions will be converted to LaTeX.

## Environment variables (backend)

- LLM_PROVIDER: openai | deepseek | ollama | azureopenai
- OPENAI_API_KEY: API key for OpenAI/DeepSeek/Azure OpenAI
- OPENAI_BASE_URL: optional base URL (e.g., https://api.deepseek.com)
- OPENAI_MODEL: model name (e.g., gpt-4o-mini, gpt-4.1-mini, deepseek-chat)
- OLLAMA_MODEL: local model name (e.g., llama3.1:8b)
- MATHPIX_APP_ID, MATHPIX_APP_KEY: Mathpix OCR credentials
- VISION_MODEL: OpenAI vision-capable model for math OCR (e.g., gpt-4o-mini)
- TESSERACT_CMD: path to tesseract executable on Windows

## Notes

- For hackathons without internet, use Ollama for local inference and Tesseract for OCR.
- Math OCR quality is best with Mathpix or a strong Vision LLM. Tesseract alone may struggle with complex equations.
- This template is intentionally simple and hackathon-friendly. Extend with vector search, streaming, and auth as needed.

## License

MIT
