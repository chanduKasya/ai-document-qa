"""Keeps uploaded documents in memory for a while.

Before, api.py had ONE shared `state`, so a second visitor's upload replaced
the first visitor's document. Now each upload gets its own random ID, and
documents are forgotten after DOCUMENT_TTL_MINUTES without use.
"""
import threading
import time
import uuid

from docqa import config

_documents = {}  # document_id -> {"filename", "pages", "chunks", "index", "last_used"}
_lock = threading.Lock()  # the server handles several requests at once; one change at a time


def _remove_expired(now):
    max_age = config.DOCUMENT_TTL_MINUTES * 60
    expired = []
    for document_id in _documents:
        if now - _documents[document_id]["last_used"] > max_age:
            expired.append(document_id)
    for document_id in expired:
        del _documents[document_id]


def _remove_least_recently_used():
    oldest_id = None
    for document_id in _documents:
        if oldest_id is None or _documents[document_id]["last_used"] < _documents[oldest_id]["last_used"]:
            oldest_id = document_id
    if oldest_id is not None:
        del _documents[oldest_id]


def save_document(filename, page_count, chunks, index):
    """Store a processed document and return its new ID."""
    now = time.time()
    # A random 32-character ID that nobody can guess, so visitors
    # can only ask about documents they uploaded themselves.
    document_id = uuid.uuid4().hex

    with _lock:
        _remove_expired(now)
        while len(_documents) >= config.MAX_DOCUMENTS:
            _remove_least_recently_used()
        _documents[document_id] = {
            "filename": filename,
            "pages": page_count,
            "chunks": chunks,
            "index": index,
            "last_used": now,
        }
    return document_id


def get_document(document_id):
    """Return the stored document, or None if it never existed or has expired."""
    now = time.time()
    with _lock:
        _remove_expired(now)
        document = _documents.get(document_id)
        if document is not None:
            document["last_used"] = now
        return document


def clear():
    """Forget every document (used by the tests)."""
    with _lock:
        _documents.clear()
