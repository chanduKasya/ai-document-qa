"""Step 3: semantic search with embeddings and FAISS.

This grew out of search_document.py. The big change: the embedding model is
loaded ONCE and reused, instead of being loaded again for every upload.
"""
import threading

import faiss
import numpy as np

from docqa import config

# A small "memory board" that holds the loaded model (same idea as `state` in api.py).
_cache = {"model": None}
_model_lock = threading.Lock()


def get_model():
    """Load the embedding model the first time, then reuse it."""
    with _model_lock:
        if _cache["model"] is None:
            # Imported here instead of at the top because it is slow to import.
            # The tests replace embed(), so they never need it.
            from sentence_transformers import SentenceTransformer

            _cache["model"] = SentenceTransformer(config.EMBEDDING_MODEL)
    return _cache["model"]


def embed(texts):
    """Turn a list of texts into a table of numbers: one row of 384 numbers per text."""
    model = get_model()
    vectors = model.encode(texts, normalize_embeddings=True)
    return np.asarray(vectors, dtype="float32")


def build_index(chunks):
    """Put every chunk's numbers on a FAISS shelf, in the same order as `chunks`."""
    texts = []
    for chunk in chunks:
        texts.append(chunk["text"])

    vectors = embed(texts)
    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)
    return index


def search(question, chunks, index, top_k):
    """Return the chunks closest in meaning to the question, best first."""
    question_vector = embed([question])
    how_many = min(top_k, len(chunks))
    scores, ids = index.search(question_vector, how_many)

    results = []
    for i in range(how_many):
        chunk_id = int(ids[0][i])
        if chunk_id < 0:  # FAISS uses -1 for "no result"
            continue
        chunk = chunks[chunk_id]
        results.append({
            "number": len(results) + 1,  # the number the AI cites, like [1]
            "page": chunk["page"],
            "score": round(float(scores[0][i]), 3),
            "text": chunk["text"],
        })
    return results
