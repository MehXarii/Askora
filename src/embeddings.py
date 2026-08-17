import os
import faiss
import numpy as np
import pickle
from sentence_transformers import SentenceTransformer
from config import FAISS_INDEX_PATH

embedder = SentenceTransformer("all-MiniLM-L6-v2")


def get_embeddings(texts: list[str]) -> np.ndarray:
    """Convert list of texts to normalized embeddings (for cosine similarity)."""
    embeddings = embedder.encode(texts, show_progress_bar=True)
    faiss.normalize_L2(embeddings)
    return embeddings


def build_faiss_index(chunks: list[dict]) -> None:
    """Build FAISS index from chunks and save to disk."""
    texts = [chunk["text"] for chunk in chunks]
    embeddings = get_embeddings(texts)

    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)  # inner product = cosine similarity (since normalized)
    index.add(np.array(embeddings))

    os.makedirs(FAISS_INDEX_PATH, exist_ok=True)
    faiss.write_index(index, f"{FAISS_INDEX_PATH}/index.faiss")

    with open(f"{FAISS_INDEX_PATH}/chunks.pkl", "wb") as f:
        pickle.dump(chunks, f)

    print(f"Index built with {len(chunks)} chunks.")


def load_faiss_index():
    index = faiss.read_index(f"{FAISS_INDEX_PATH}/index.faiss")
    with open(f"{FAISS_INDEX_PATH}/chunks.pkl", "rb") as f:
        chunks = pickle.load(f)
    return index, chunks


def search_index(query: str, index, chunks: list[dict], top_k: int = 5) -> list[dict]:
    """Search FAISS index and return top_k relevant chunks with similarity scores."""
    query_embedding = embedder.encode([query])
    faiss.normalize_L2(query_embedding)
    scores, indices = index.search(np.array(query_embedding), top_k)

    results = []
    for i, idx in enumerate(indices[0]):
        if idx != -1:
            chunk = chunks[idx].copy()
            chunk["score"] = float(scores[0][i])  # now a similarity score (higher = better)
            results.append(chunk)

    return results


def index_exists() -> bool:
    return os.path.exists(f"{FAISS_INDEX_PATH}/index.faiss")