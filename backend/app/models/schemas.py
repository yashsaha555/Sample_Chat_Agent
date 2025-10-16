from pydantic import BaseModel
from typing import List, Optional


class ChatRequest(BaseModel):
    message: str
    system: Optional[str] = "You are a helpful assistant."
    context: Optional[List[str]] = None  # extracted texts from uploads


class ChatResponse(BaseModel):
    reply: str


class UploadedItem(BaseModel):
    filename: str
    content: str


class UploadResponse(BaseModel):
    items: List[UploadedItem]
