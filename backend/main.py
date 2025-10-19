import os
import io
import uuid
from typing import List, Optional

from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import requests
from pypdf import PdfReader

# Disable Chroma telemetry globally to avoid PostHog capture errors
os.environ.setdefault("CHROMA_TELEMETRY_ENABLED", "false")

# Load env vars from .env if present (so OPENROUTER_API_KEY can be set there)
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

import chromadb
from chromadb.utils import embedding_functions
from chromadb.api.models.Collection import Collection
from chromadb.config import Settings

try:
    from fastembed import TextEmbedding
except Exception:
    TextEmbedding = None  # type: ignore

# -----------------
# Config
# -----------------
APP_PORT = int(os.getenv("PORT", "8000"))
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL")
CHROMA_PATH = os.path.join(os.path.dirname(__file__), "chroma_db")
COLLECTION_NAME = "atomic-habits"
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
PDF_PATH = os.path.join(PROJECT_ROOT, "Atomic habits ( PDFDrive ).pdf")

# -----------------
# App
# -----------------
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------
# Embeddings + Vector DB
# -----------------

class FastEmbedEmbeddingFunction:
    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5") -> None:
        if TextEmbedding is None:
            raise RuntimeError("fastembed is not installed. Please install requirements.")
        self._model = TextEmbedding(model_name=model_name)

    def __call__(self, input: List[str]):  # Chroma expects param name 'input'
        # Convert to plain Python lists to satisfy Chroma requirements
        return [vec.tolist() for vec in self._model.embed(input)]

_client: Optional[chromadb.PersistentClient] = None
_collection: Optional[Collection] = None


def get_client() -> chromadb.PersistentClient:
    global _client
    if _client is None:
        os.makedirs(CHROMA_PATH, exist_ok=True)
        _client = chromadb.PersistentClient(path=CHROMA_PATH, settings=Settings(anonymized_telemetry=False))
    return _client


def get_collection() -> Collection:
    global _collection
    if _collection is None:
        ef = FastEmbedEmbeddingFunction()
        _collection = get_client().get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=ef,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


# -----------------
# Utils
# -----------------

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    chunks: List[str] = []
    start = 0
    n = len(text)
    if chunk_size <= 0:
        return [text]
    while start < n:
        end = min(n, start + chunk_size)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == n:
            break
        start = end - overlap
        if start < 0:
            start = 0
    return chunks

def add_batched(col: Collection, ids: List[str], documents: List[str], metadatas: List[dict], batch_size: int = 100) -> None:
    n = len(documents)
    for i in range(0, n, batch_size):
        j = i + batch_size
        col.add(ids=ids[i:j], documents=documents[i:j], metadatas=metadatas[i:j])


def extract_text_from_pdf(file_obj: io.BytesIO) -> str:
    reader = PdfReader(file_obj)
    texts: List[str] = []
    for page in reader.pages:
        try:
            t = page.extract_text() or ""
        except Exception:
            t = ""
        if t:
            texts.append(t)
    return "\n".join(texts)


def build_system_prompt() -> str:
    return (
        "You are a grounded RAG assistant.\n"
        "- Only answer using the provided CONTEXT. Do not use external knowledge.\n"
        "- If the answer is not present or you are unsure, reply: 'I don't know based on the provided context.'\n"
        "- If the question is outside of the topics of Atomic Habits (James Clear) or the supplied logs, say it's out of scope.\n"
        "- Be concise. When useful, structure the answer with short bullets.\n"
    )


def call_openrouter(messages: List[dict], temperature: float = 0.2, max_tokens: int = 512) -> str:
    api_key = OPENROUTER_API_KEY or os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Missing OPENROUTER_API_KEY. Set environment variable OPENROUTER_API_KEY to your OpenRouter key."
        )
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        # Optional best-practices headers, not required
        "HTTP-Referer": os.getenv("OPENROUTER_SITE_URL", "http://localhost"),
        "X-Title": os.getenv("OPENROUTER_TITLE", "RAG Chatbot"),
    }
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    r = requests.post(url, headers=headers, json=payload, timeout=120)
    if r.status_code != 200:
        raise RuntimeError(f"OpenRouter error {r.status_code}: {r.text}")
    js = r.json()
    try:
        return js["choices"][0]["message"]["content"].strip()
    except Exception:
        raise RuntimeError(f"Unexpected OpenRouter response schema: {js}")


# -----------------
# Schemas
# -----------------
class ChatBody(BaseModel):
    message: str
    context: Optional[List[str]] = None


# -----------------
# Endpoints
# -----------------

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/api/generate-dataset")
def generate_dataset():
    if not os.path.exists(PDF_PATH):
        return JSONResponse(status_code=400, content={"error": f"PDF not found at {PDF_PATH}"})

    # Recreate collection for idempotency
    client = get_client()
    try:
        client.delete_collection(COLLECTION_NAME)  # type: ignore
    except Exception:
        pass

    # Reset cached handle to avoid stale refs after delete
    global _collection
    _collection = None

    col = get_collection()  # re-creates

    # Read and chunk PDF
    with open(PDF_PATH, "rb") as f:
        text = extract_text_from_pdf(io.BytesIO(f.read()))
    if not text.strip():
        return JSONResponse(status_code=400, content={"error": "No text extracted from PDF"})

    chunks = chunk_text(text, chunk_size=1200, overlap=200)

    ids = [f"atomic-{i}" for i in range(len(chunks))]
    metadatas = [{"source": "Atomic Habits (PDFDrive)", "chunk": i} for i in range(len(chunks))]

    add_batched(col, ids, chunks, metadatas, batch_size=100)

    return {"status": "ok", "items": len(chunks)}


@app.get("/api/status")
def status():
    pdf_found = os.path.exists(PDF_PATH)
    openrouter_configured = bool(OPENROUTER_API_KEY or os.getenv("OPENROUTER_API_KEY"))
    model = OPENROUTER_MODEL
    collection_exists = False
    doc_count: Optional[int] = None
    try:
        client = get_client()
        for meta in client.list_collections():
            if getattr(meta, "name", None) == COLLECTION_NAME:
                collection_exists = True
                break
        if collection_exists:
            try:
                col = get_collection()
                doc_count = col.count()  # type: ignore
            except Exception:
                doc_count = None
    except Exception:
        pass
    return {
        "pdf_found": pdf_found,
        "openrouter_configured": openrouter_configured,
        "openrouter_model": model,
        "collection_exists": collection_exists,
        "doc_count": doc_count,
    }

@app.post("/api/upload")
def upload(files: List[UploadFile] = File(...)):
    items = []
    for uf in files:
        content_text = ""
        try:
            data = uf.file.read()
            if uf.filename and uf.filename.lower().endswith(".pdf"):
                content_text = extract_text_from_pdf(io.BytesIO(data))
            else:
                try:
                    content_text = data.decode("utf-8", errors="ignore")
                except Exception:
                    content_text = ""
        finally:
            uf.file.close()
        items.append({"filename": uf.filename, "content": content_text.strip()[:20000]})
    return {"items": items}


@app.post("/api/chat")
def chat(body: ChatBody):
    message = (body.message or "").strip()
    if not message:
        return JSONResponse(status_code=400, content={"error": "Empty message"})

    user_ctx = body.context or []

    # Retrieve from vector DB
    try:
        col = get_collection()
        q = col.query(query_texts=[message], n_results=5, include=["documents", "metadatas", "distances"])  # type: ignore
        retrieved_docs: List[str] = []
        distances: List[float] = []
        if q and q.get("documents"):
            retrieved_docs = [d for d in q["documents"][0] if isinstance(d, str)]
            distances = [float(x) for x in (q.get("distances", [[1.0]])[0] or [])]
    except Exception:
        retrieved_docs, distances = [], []

    top_distance = distances[0] if distances else 1.0

    # Guardrails: if no user context and retrieval is poor, decline
    allow_rag = True
    if not user_ctx and (not retrieved_docs or top_distance > 0.4):  # lower is closer for cosine distance in HNSW
        allow_rag = False

    system_prompt = build_system_prompt()

    context_blocks: List[str] = []
    if allow_rag and retrieved_docs:
        context_blocks.append("\n\n".join(retrieved_docs[:5]))
    if user_ctx:
        context_blocks.append("\n\n".join(user_ctx[:5]))

    # If still no context, answer with refusal without calling LLM (guardrail)
    if not context_blocks:
        reply = (
            "I don't know based on the provided context. Please generate the dataset or upload relevant files."
        )
        return {"reply": reply}

    final_context = "\n\n".join(context_blocks)

    user_prompt = (
        "CONTEXT:\n" + final_context + "\n\n" +
        "USER QUESTION:\n" + message + "\n\n" +
        "Instructions: Base your answer strictly on the CONTEXT. If not present, say you don't know."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    api_key_present = bool(OPENROUTER_API_KEY or os.getenv("OPENROUTER_API_KEY"))
    if not api_key_present:
        return {"reply": "LLM is not configured. Set OPENROUTER_API_KEY in backend/.env and restart the server."}

    try:
        answer = call_openrouter(messages, temperature=0.2, max_tokens=700)
    except Exception as e:
        return {"reply": f"Unable to generate answer: {str(e)}"}

    return {"reply": answer}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=APP_PORT)
