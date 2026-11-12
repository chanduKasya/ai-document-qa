"""The web server: the API routes plus the web page in /static.

This grew out of api.py. Run it with:
    python -m uvicorn docqa.main:app --reload
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from docqa import config, documents, search
from docqa.llm import LLMError, generate_answer
from docqa.pdf_reader import DocumentError
from docqa.pipeline import build_document
from docqa.rate_limit import RateLimiter

ONE_HOUR = 60 * 60

upload_limiter = RateLimiter(config.UPLOADS_PER_CLIENT_PER_HOUR, ONE_HOUR)
question_limiter = RateLimiter(config.QUESTIONS_PER_CLIENT_PER_HOUR, ONE_HOUR)
total_question_limiter = RateLimiter(config.QUESTIONS_PER_HOUR_TOTAL, ONE_HOUR)


@asynccontextmanager
async def lifespan(app):
    # Load the embedding model once when the server starts,
    # so the first visitor doesn't have to wait for it.
    if config.PRELOAD_MODEL:
        search.get_model()
    yield


app = FastAPI(
    title="Document Q&A",
    description="Upload a PDF and ask questions. Answers cite the pages they came from.",
    version="1.0.0",
    lifespan=lifespan,
)


class AskRequest(BaseModel):
    question: str


def client_key(request):
    """Best guess at who is calling, for the per-visitor limits.

    Behind a hosting proxy, request.client.host is the proxy, so we read the
    X-Forwarded-For header that the proxy adds. The last address in it is the
    one our own proxy added. It isn't perfect, which is why there is also an
    overall hourly limit on questions.
    """
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded.strip() != "":
        parts = forwarded.split(",")
        return parts[-1].strip()
    if request.client is not None:
        return request.client.host
    return "unknown"


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/limits")
def limits():
    """The web page reads these so its hints always match the server."""
    return {
        "max_upload_mb": config.MAX_UPLOAD_MB,
        "max_pages": config.MAX_PAGES,
        "max_question_chars": config.MAX_QUESTION_CHARS,
        "document_ttl_minutes": config.DOCUMENT_TTL_MINUTES,
    }


@app.post("/api/documents")
def upload_document(request: Request, file: UploadFile = File(...)):
    if not upload_limiter.allow(client_key(request)):
        raise HTTPException(status_code=429, detail="Too many uploads. Try again in an hour.")

    max_bytes = config.MAX_UPLOAD_MB * 1024 * 1024
    data = file.file.read(max_bytes + 1)  # read one byte past the limit to detect big files
    if len(data) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail="This file is larger than " + str(config.MAX_UPLOAD_MB) + " MB.",
        )
    if len(data) == 0:
        raise HTTPException(status_code=400, detail="This file is empty.")

    try:
        pages, chunks, index = build_document(data)
    except DocumentError as error:
        raise HTTPException(status_code=400, detail=str(error))

    filename = file.filename or "document.pdf"
    filename = filename[:120]
    document_id = documents.save_document(filename, len(pages), chunks, index)

    return {
        "document_id": document_id,
        "filename": filename,
        "pages": len(pages),
        "chunks": len(chunks),
        "expires_after_minutes_unused": config.DOCUMENT_TTL_MINUTES,
    }


@app.post("/api/documents/{document_id}/ask")
def ask(document_id: str, body: AskRequest, request: Request):
    question = body.question.strip()
    if question == "":
        raise HTTPException(status_code=400, detail="Type a question first.")
    if len(question) > config.MAX_QUESTION_CHARS:
        raise HTTPException(
            status_code=400,
            detail="Questions can be up to " + str(config.MAX_QUESTION_CHARS) + " characters.",
        )

    document = documents.get_document(document_id)
    if document is None:
        raise HTTPException(
            status_code=404,
            detail="This document has expired or was never uploaded. Upload it again.",
        )

    if not question_limiter.allow(client_key(request)):
        raise HTTPException(status_code=429, detail="Too many questions. Try again in an hour.")
    if not total_question_limiter.allow("everyone"):
        raise HTTPException(
            status_code=429,
            detail="This demo has reached its hourly question limit. Try again later.",
        )

    results = search.search(question, document["chunks"], document["index"], config.TOP_K)

    try:
        answer = generate_answer(question, results)
    except LLMError as error:
        raise HTTPException(status_code=502, detail=str(error))

    return {"answer": answer, "sources": results}


# The web page. Mounted last, so the /api routes above are matched first.
app.mount("/", StaticFiles(directory=config.STATIC_DIR, html=True), name="static")
