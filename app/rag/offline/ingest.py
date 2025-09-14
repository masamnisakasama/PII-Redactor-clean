from pathlib import Path
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_huggingface import HuggingFaceEmbeddings          # ★ここを変更
from langchain_community.vectorstores import FAISS
from app.rag.common.textsplit import make_splitter

REPO_ROOT = Path(__file__).resolve().parents[3]
APP_DIR   = REPO_ROOT / "app"
INDEX_DIR = REPO_ROOT / "vectorstore"
INDEX_DIR.mkdir(exist_ok=True)

def load_docs():
    docs = []
    rd = REPO_ROOT / "README.md"
    if rd.exists():
        docs += TextLoader(str(rd), autodetect_encoding=True).load()
    if APP_DIR.exists():
        for pat in ["**/*.py", "**/*.md"]:
            loader = DirectoryLoader(
                str(APP_DIR), glob=pat, use_multithreading=True,
                loader_cls=TextLoader, silent_errors=True
            )
            docs += loader.load()
    return docs

def build_index():
    docs = load_docs()
    chunks = make_splitter().split_documents(docs)
    emb = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")  # ★変更
    vs = FAISS.from_documents(chunks, emb)
    vs.save_local(str(INDEX_DIR), index_name="index")  # ★index名を明示
    return len(chunks)

if __name__ == "__main__":
    n = build_index()
    print(f"[RAG] built index: {n} chunks -> {INDEX_DIR}")
