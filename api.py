from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException 
from pydantic import BaseModel


from answer_question import build_index, retrieve_chunks, build_context, generate_answer
from pipeline import build_from_pdf
from search_document import load_chunks, CHUNKS_PATH
from chunker import split_into_chunks

PROJECT_ROOT = Path(__file__). resolve().parent
UPLOAD_PATH = PROJECT_ROOT / "data" /"uploaded.pdf"
MAX_UPLOAD_BYTES = 10 * 1024 * 1024


app = FastAPI()

state = {"chunks": [], "model": None, "index": None}

class AskRequest(BaseModel):
    question: str

@app.get("/")
def home():
    return {"message": "Document Q&A API is running"}


@app.post("/upload")
def upload(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail = "Please upload a PDF file")

    data = file.file.read(MAX_UPLOAD_BYTES + 1)
    if len(data)> MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail = "File is too large(max 10 MB).")
    
    UPLOAD_PATH.write_bytes(data)

    try:
        pages = extract_text_from_pdf(UPLOAD_PATH)
    except Exception:
        raise HTTPException(status_code=400, detail = "Could not read this PDF.")

    full_text = ""
    for page in pages:
        full_text = full_text + page["text"] + "\n"

    if full_text.strip() == "":
        raise HTTPException(status_code = 400, detail = "No text found. The PDF may be scanne images.")

    chunks = split_into_chunks(full_text, CHUNK_SIZE, OVERLAP)
    model,index = build_index(chunks)

    state["chunks"] = chunks
    state["model"] = model
    state["index"] = index

    return {"filename": file.filename, "pages": len(pages), "chunks": len(chunks)}


@app.post("/ask")
def ask(request: AskRequest):
    if state["index"] is None:
        raise HTTPException(status_code=400, detail = "Upload a pdf first using /upload.")
    results = retrieve_chunks(request.question, state["chunks"], state["model"], state["index"] )
    try:
        answer = generate_answer(request.question, build_context(results))
    except Exception:
        raise HTTPException(status_code = 502, detail = "The AI service failed. Try again.")


    return {"answer": answer , "sources": results}




