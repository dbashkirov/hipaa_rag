from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Any

from rag_graph import answer

app = FastAPI(title="HIPAA-RAG")

class ChatRequest(BaseModel):
    question: str

class ChatResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    used_retrieval: bool

@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    return answer(req.question)

@app.get("/api/health")
async def health():
    return {"status": "ok"}
