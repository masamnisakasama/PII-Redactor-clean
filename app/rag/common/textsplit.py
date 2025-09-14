import os
from langchain_text_splitters import RecursiveCharacterTextSplitter

def make_splitter():
    return RecursiveCharacterTextSplitter(
        chunk_size=int(os.getenv("RAG_CHUNK_SIZE", "1200")),
        chunk_overlap=int(os.getenv("RAG_CHUNK_OVERLAP", "180")),
    )
