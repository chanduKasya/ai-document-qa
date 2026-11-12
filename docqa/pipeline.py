"""Turns an uploaded PDF into a searchable document: read, chunk, index.

This is pipeline.py from the Streamlit version, now working on bytes in memory.
"""
from docqa import config
from docqa.chunker import chunk_pages
from docqa.pdf_reader import DocumentError, read_pdf_pages
from docqa.search import build_index


def build_document(pdf_bytes):
    """Return (pages, chunks, index) for a PDF, or raise DocumentError."""
    pages = read_pdf_pages(pdf_bytes, config.MAX_PAGES)
    chunks = chunk_pages(pages, config.CHUNK_SIZE, config.OVERLAP)

    if len(chunks) == 0:
        raise DocumentError(
            "No text found in this PDF. It may be scanned images, which this app can't read yet."
        )

    index = build_index(chunks)
    return pages, chunks, index
