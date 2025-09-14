# app/rag/offline/retriever.py
from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, List

from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

# リポ直下の vectorstore を指す（…/PII-Redactor-clean/vectorstore）
REPO_ROOT = Path(__file__).resolve().parents[3]
INDEX_DIR = REPO_ROOT / "vectorstore"
INDEX_NAME = "index"

def _assert_index_exists() -> None:
    faiss_p = INDEX_DIR / f"{INDEX_NAME}.faiss"
    meta_p  = INDEX_DIR / f"{INDEX_NAME}.pkl"
    if not faiss_p.exists() or not meta_p.exists():
        raise FileNotFoundError(
            f"Vector index not found at: {INDEX_DIR}\n"
            f"Expected files: {faiss_p.name}, {meta_p.name}\n"
            "Build it first with: `python -m app.rag.offline.ingest`"
        )

def _embeddings() -> HuggingFaceEmbeddings:
    # 依存: pip install langchain-huggingface
    return HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

def _retriever():
    _assert_index_exists()
    emb = _embeddings()
    vs = FAISS.load_local(
        str(INDEX_DIR),
        emb,
        index_name=INDEX_NAME,
        allow_dangerous_deserialization=True,  # ローカル運用前提
    )
    # MMR で冗長性を下げつつ多様性確保
    return vs.as_retriever(
        search_type="mmr",
        search_kwargs={"k": 6, "fetch_k": 20, "lambda_mult": 0.5},
    )

def ask(q: str, k: int = 6) -> Dict[str, Any]:
    """
    最小RAG（生成なし）:
      - FAISS (ローカル) から関連コンテキストを取得して返す
      - 失敗時は親切なエラーを辞書で返す（ルーター側でそのままJSON化できる）
    """
    try:
        r = _retriever()
        docs = r.get_relevant_documents(q)
        items: List[Dict[str, str]] = []
        for d in docs[: max(1, k)]:
            items.append(
                {
                    "source": d.metadata.get("source", ""),
                    "content": (d.page_content or "")[:800],
                }
            )
        return {"answer": "(context only)", "contexts": items}
    except FileNotFoundError as e:
        return {
            "error": "vectorstore_not_found",
            "detail": str(e),
            "index_dir": str(INDEX_DIR),
        }
    except Exception as e: 
        return {
            "error": "retriever_runtime_error",
            "detail": repr(e),
            "index_dir": str(INDEX_DIR),
        }

__all__ = ["ask", "INDEX_DIR"]
