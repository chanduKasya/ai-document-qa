from conftest import make_pdf
from docqa import main
from docqa.llm import LLMError
from docqa.rate_limit import RateLimiter

HANDBOOK = make_pdf([
    "Working hours are 10:30 to 16:30. You can work from home three days a week.",
    "Everyone gets 24 days of paid leave a year, plus public holidays.",
])


def upload(client, data=HANDBOOK, name="handbook.pdf"):
    return client.post("/api/documents", files={"file": (name, data, "application/pdf")})


def ask(client, document_id, question):
    return client.post("/api/documents/" + document_id + "/ask", json={"question": question})


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_web_page_is_served(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Document Q&amp;A" in response.text


def test_upload_then_ask_returns_answer_with_pages(client):
    response = upload(client)
    assert response.status_code == 200
    document = response.json()
    assert document["pages"] == 2
    assert document["chunks"] == 2
    assert document["filename"] == "handbook.pdf"

    response = ask(client, document["document_id"], "How many days of paid leave?")
    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "Employees get 24 days of paid leave [1]."
    assert data["sources"][0]["page"] == 2  # the leave text is on page 2
    assert data["sources"][0]["number"] == 1


def test_each_upload_gets_its_own_document(client):
    first = upload(client).json()["document_id"]
    second = upload(client, make_pdf(["A different document about bicycles."])).json()["document_id"]
    assert first != second
    sources = ask(client, first, "paid leave").json()["sources"]
    assert any("paid leave" in source["text"] for source in sources)


def test_rejects_non_pdf(client):
    response = upload(client, b"just some text", "notes.txt")
    assert response.status_code == 400
    assert response.json()["detail"] == "This file is not a PDF."


def test_rejects_pdf_without_text(client):
    response = upload(client, make_pdf([""]))
    assert response.status_code == 400
    assert "No text found" in response.json()["detail"]


def test_rejects_empty_file(client):
    response = upload(client, b"")
    assert response.status_code == 400


def test_rejects_large_file(client, monkeypatch):
    monkeypatch.setattr(main.config, "MAX_UPLOAD_MB", 0)
    response = upload(client)
    assert response.status_code == 413


def test_unknown_document_is_404(client):
    response = ask(client, "does-not-exist", "Hello?")
    assert response.status_code == 404


def test_blank_and_long_questions_are_rejected(client):
    document_id = upload(client).json()["document_id"]
    assert ask(client, document_id, "   ").status_code == 400
    assert ask(client, document_id, "x" * 501).status_code == 400


def test_question_rate_limit(client, monkeypatch):
    monkeypatch.setattr(main, "question_limiter", RateLimiter(2, 3600))
    document_id = upload(client).json()["document_id"]
    assert ask(client, document_id, "one").status_code == 200
    assert ask(client, document_id, "two").status_code == 200
    response = ask(client, document_id, "three")
    assert response.status_code == 429


def test_ai_failure_is_502_with_message(client, monkeypatch):
    def broken_answer(question, results):
        raise LLMError("The AI service did not respond. Try again in a moment.")

    monkeypatch.setattr(main, "generate_answer", broken_answer)
    document_id = upload(client).json()["document_id"]
    response = ask(client, document_id, "How much leave?")
    assert response.status_code == 502
    assert "did not respond" in response.json()["detail"]
