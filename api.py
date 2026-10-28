from fastapi import FastAPI
from pydantic import BaseModel


from answer_question import build_index, retrieve_chunks, build_context, generate_answer
from search_document import load_chunks, CHUNKS_PATH

app = FastAPI()

chunks = load_chunks(CHUNKS_PATH)
model, index = build_index(chunks)

class AskRequest(BaseModel):
    question: str

@app.get("/")
def home():
    return {"message": "Document Q&A API is running"}


@app.post("/ask")
def ask(request: AskRequest):
    results = retrieve_chunks(request.question, chunks, model,index)
    answer = generate_answer(request.question, build_context(results))
    return{"answer": answer, "sources": results}

