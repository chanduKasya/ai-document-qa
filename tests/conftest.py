"""Shared test setup.

The tests never download the real embedding model or call Groq:
- fake_embed() gives each text a simple word-count fingerprint instead.
- The AI answer is replaced with a fixed reply.
That keeps the tests fast, free and runnable without internet.
"""
import hashlib
import os
import re

# These must be set before docqa is imported, because config reads them at import time.
os.environ["PRELOAD_MODEL"] = "0"
os.environ["LLM_API_KEY"] = "test-key"

import numpy as np  # noqa: E402
import pymupdf  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from docqa import documents, main, search  # noqa: E402
from docqa.rate_limit import RateLimiter  # noqa: E402

DIMENSIONS = 64


def fake_embed(texts):
    """Same idea as real embeddings (texts sharing words get similar numbers), with no model."""
    vectors = np.zeros((len(texts), DIMENSIONS), dtype="float32")
    for row in range(len(texts)):
        words = re.findall(r"[a-z0-9]+", texts[row].lower())
        for word in words:
            bucket = int(hashlib.md5(word.encode()).hexdigest(), 16) % DIMENSIONS
            vectors[row, bucket] += 1.0
        length = np.linalg.norm(vectors[row])
        if length > 0:
            vectors[row] = vectors[row] / length
    return vectors


def make_pdf(page_texts):
    """Build a small PDF in memory, one page per text."""
    pdf = pymupdf.open()
    for text in page_texts:
        page = pdf.new_page()
        page.insert_textbox(pymupdf.Rect(72, 72, 540, 770), text, fontsize=11)
    data = pdf.tobytes()
    pdf.close()
    return data


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(search, "embed", fake_embed)

    def fake_answer(question, results):
        return "Employees get 24 days of paid leave [1]."

    monkeypatch.setattr(main, "generate_answer", fake_answer)

    # Fresh limits and an empty document store for every test.
    monkeypatch.setattr(main, "upload_limiter", RateLimiter(100, 3600))
    monkeypatch.setattr(main, "question_limiter", RateLimiter(100, 3600))
    monkeypatch.setattr(main, "total_question_limiter", RateLimiter(100, 3600))
    documents.clear()

    with TestClient(main.app) as test_client:
        yield test_client

    documents.clear()
