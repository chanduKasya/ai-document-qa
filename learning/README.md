# Learning scripts

These are the step-by-step scripts the app in `docqa/` grew out of. They are kept to show how the project was built. The app does not use them.

| Script | What it did |
|---|---|
| `extract_pdf.py` | Read `data/sample.pdf` and saved its text to `data/extracted_text.txt` |
| `chunker.py` | Split that text into overlapping chunks in `data/chunks.txt` |
| `search_document.py` | Searched the chunks by meaning in the terminal |
| `answer_question.py` | Answered questions in the terminal with Groq |
| `app.py` | First web page, built with Streamlit |
| `api.py`, `pipeline.py` | First FastAPI version, with one shared document |
| `embed_test.py`, `groq_test.py` | Small experiments with embeddings and the Groq API |

They read and write files in a `data/` folder next to them, and `app.py` also needs `pip install streamlit`.
