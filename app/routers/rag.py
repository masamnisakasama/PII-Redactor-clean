from fastapi import APIRouter, Form
from app.rag.offline.ingest import build_index
from app.rag.offline.retriever import ask as offline_ask

router = APIRouter(prefix="/rag", tags=["rag"])

@router.post("/offline/reindex")
def reindex_offline():
    n = build_index()
    return {"status": "ok", "chunks": n}

@router.post("/offline/ask")
def rag_offline_ask(q: str = Form(...), k: int = Form(6)):
    # 生成LLMなし：関連文脈（抜粋）を返すシンプル版
    result = offline_ask(q, k=k)
    return result
