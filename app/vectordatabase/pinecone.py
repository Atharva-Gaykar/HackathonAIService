import os
import json
import requests
import pickle
from typing import List
from pathlib import Path
from pinecone import Pinecone, ServerlessSpec
from pinecone_text.sparse import BM25Encoder
from langchain_community.retrievers import PineconeHybridSearchRetriever
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from app.core.config import settings

# 1. Path Resolution (Fixes the folder structure issue)
# This finds the absolute path to the directory containing this file
current_file_path = Path(__file__).resolve()
VDB_DIR = current_file_path.parent
BASE_DATA_DIR = VDB_DIR / "ComplaintData"

# Pickle files will now be stored inside the vectordatabase folder too
PRIORITY_BM25_PKL = VDB_DIR / "priority_bm25.pkl"
MATCHING_BM25_PKL = VDB_DIR / "matching_data_bm25.pkl"

# 2. Environment & API Setup
PINECONE_API_KEY = settings.PINECONE_API_KEY
if not PINECONE_API_KEY:
    raise ValueError("PINECONE_API_KEY not found in settings.")

pc = Pinecone(api_key=PINECONE_API_KEY)

# 3. Remote Embedding Configuration
class GeneralRemoteEmbeddings(Embeddings):
    def __init__(self, endpoint: str):
        self.endpoint = endpoint

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        response = requests.post(f"{self.endpoint}/embed_docs", json={"texts": texts})
        response.raise_for_status()
        return response.json()["embeddings"]

    def embed_query(self, text: str) -> List[float]:
        response = requests.post(f"{self.endpoint}/embed_query", json={"text": text})
        response.raise_for_status()
        return response.json()["embedding"]

embeddings = GeneralRemoteEmbeddings(endpoint="https://gaykar-generalembeddings.hf.space")

# 4. Index Initialization Helper
def get_or_create_index(name: str):
    if name not in pc.list_indexes().names():
        pc.create_index(
            name=name,
            dimension=384,
            metric="dotproduct",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )
    return pc.Index(name)

index_general = get_or_create_index("complaints-index")
index_matching = get_or_create_index("user-complaint-matching-index")

# 5. Data Loading Logic
def load_docs_from_json(pattern: str):
    docs = []
    # Search inside the absolute path resolved in step 1
    for file_path in BASE_DATA_DIR.glob(pattern):
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                for item in data:
                    docs.append(Document(
                        page_content=item.get("page_content", ""),
                        metadata=item.get("metadata", {})
                    ))
            except Exception as e:
                print(f"Error loading {file_path}: {e}")
    return docs

# --- 6. BM25 & Retriever Setup for Priority Scoring ---
general_docs = load_docs_from_json("*_langchain_formatted.json")
bm25_general = BM25Encoder()

if PRIORITY_BM25_PKL.exists():
    with open(PRIORITY_BM25_PKL, "rb") as f:
        bm25_general = pickle.load(f)
else:
    # IMPORTANT: Always fit on at least one string to prevent "not fit" error
    texts = [doc.page_content for doc in general_docs] if general_docs else ["seed text for priority"]
    bm25_general.fit(texts)
    with open(PRIORITY_BM25_PKL, "wb") as f:
        pickle.dump(bm25_general, f)

retriever = PineconeHybridSearchRetriever(
    embeddings=embeddings,
    sparse_encoder=bm25_general,
    index=index_general,
    alpha=0.85
)

# --- 7. BM25 & Retriever Setup for Duplicate Matching ---
matching_docs = load_docs_from_json("complaint_matching_data.json")
bm25_matching = BM25Encoder()

if MATCHING_BM25_PKL.exists():
    with open(MATCHING_BM25_PKL, "rb") as f:
        bm25_matching = pickle.load(f)
else:
    # Safety fit for matching retriever
    texts = [doc.page_content for doc in matching_docs] if matching_docs else ["seed text for matching"]
    bm25_matching.fit(texts)
    with open(MATCHING_BM25_PKL, "wb") as f:
        pickle.dump(bm25_matching, f)

matching_retriever = PineconeHybridSearchRetriever(
    embeddings=embeddings,
    sparse_encoder=bm25_matching,
    index=index_matching,
    top_k=1,
    alpha=0.9
)