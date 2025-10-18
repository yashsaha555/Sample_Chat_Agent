import os
import io
import re
import uuid
from typing import List, Optional

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from .rag import RAGAgent
from .security import sanitize_text, is_in_domain
from .utils import read_text_file

load_dotenv()

app = FastAPI(title="IoT Diagnostics Agent API")

# CORS for local frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Initialize RAG agent (lazy)
_agent: Optional[RAGAgent] = None

def get_agent() -> RAGAgent:
    global _agent
    if _agent is None:
        _agent = RAGAgent()
    return _agent

class ChatRequest(BaseModel):
    message: str
    context: Optional[List[str]] = None

class ChatResponse(BaseModel):
    reply: str

@app.post("/api/upload")
async def upload(files: List[UploadFile] = File(...)):
    # Guardrail: file type and size limits
    items = []
    for f in files:
        if f.content_type not in ("text/plain", "application/octet-stream", "application/txt"):
            continue
        content_bytes = await f.read()
        text = content_bytes.decode("utf-8", errors="ignore")
        text = sanitize_text(text)
        if not is_in_domain(text):
            # Skip out-of-domain content
            continue
        items.append({"filename": f.filename, "content": text[:20000]})
    return {"items": items}

@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    message = sanitize_text(req.message or "")
    if not is_in_domain(message):
        return ChatResponse(reply="Your input appears outside vehicle IoT diagnostics. Please provide motor vehicle IoT logs or status queries.")

    agent = get_agent()
    # Merge any uploaded context chunks
    context_docs = req.context or []

    reply = agent.answer(message, context_docs=context_docs)
    return ChatResponse(reply=reply)

@app.post("/api/generate-dataset")
async def generate_dataset():
    agent = get_agent()
    n = agent.build_and_ingest_synthetic_dataset()
    return {"ingested": n}

@app.post("/api/generate-sample-logs")
async def generate_sample_logs(count: int = 5):
    agent = get_agent()
    items = agent.generate_sample_logs(count=count)
    return {"items": items}

@app.get("/api/health")
async def health():
    return {"status": "ok"}
