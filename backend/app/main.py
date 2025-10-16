import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List

from .models.schemas import ChatRequest, ChatResponse, UploadResponse
from .services.llm_providers import LLMClient, get_llm_client
from .services.doc_processing import extract_text_from_file
from .services.ocr import extract_text_from_image, extract_math_from_image

app = FastAPI(title="Hackathon Chatbot API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    provider = os.getenv("LLM_PROVIDER", "unset")
    return {"status": "ok", "provider": provider}


@app.post("/api/upload", response_model=UploadResponse)
async def upload_files(files: List[UploadFile] = File(...)):
    texts = []
    for f in files:
        try:
            if f.content_type.startswith("image/"):
                image_bytes = await f.read()
                text = await extract_text_from_image(image_bytes)
                # Try math extraction (best-effort)
                math = await extract_math_from_image(image_bytes)
                if math:
                    text = text + "\n\n[Math OCR]\n" + math
            else:
                text = await extract_text_from_file(f)
            texts.append({"filename": f.filename, "content": text})
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to process {f.filename}: {e}")
    return UploadResponse(items=texts)


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    try:
        client: LLMClient = get_llm_client()
        content = req.message
        # Append uploaded text context if provided
        if req.context:
            content = content + "\n\nContext from files:\n" + "\n---\n".join(req.context)
        result = await client.chat(content, system=req.system)
        return ChatResponse(reply=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
