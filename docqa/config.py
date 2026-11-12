"""All settings in one place.

Every value can be changed with an environment variable of the same name,
so the server can be tuned without editing code.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATIC_DIR = PROJECT_ROOT / "static"

# On your computer, settings come from the .env file.
# On a server, the same names are set as environment variables ("secrets").
load_dotenv(PROJECT_ROOT / ".env")


def read_int(name, default):
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return int(value)


# The AI that writes the answers (Groq)
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")
LLM_TIMEOUT_SECONDS = read_int("LLM_TIMEOUT_SECONDS", 30)

# The model that turns text into numbers. It runs on our own server.
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
PRELOAD_MODEL = os.getenv("PRELOAD_MODEL", "1") == "1"

# Chunking and search
CHUNK_SIZE = read_int("CHUNK_SIZE", 100)  # words per chunk
OVERLAP = read_int("OVERLAP", 20)  # words shared with the next chunk
TOP_K = read_int("TOP_K", 5)  # passages sent to the AI per question

# Limits that protect the server and the Groq quota
MAX_UPLOAD_MB = read_int("MAX_UPLOAD_MB", 10)
MAX_PAGES = read_int("MAX_PAGES", 100)
MAX_QUESTION_CHARS = read_int("MAX_QUESTION_CHARS", 500)
MAX_DOCUMENTS = read_int("MAX_DOCUMENTS", 50)  # documents kept in memory at once
DOCUMENT_TTL_MINUTES = read_int("DOCUMENT_TTL_MINUTES", 60)  # forgotten after this long unused
UPLOADS_PER_CLIENT_PER_HOUR = read_int("UPLOADS_PER_CLIENT_PER_HOUR", 10)
QUESTIONS_PER_CLIENT_PER_HOUR = read_int("QUESTIONS_PER_CLIENT_PER_HOUR", 30)
QUESTIONS_PER_HOUR_TOTAL = read_int("QUESTIONS_PER_HOUR_TOTAL", 300)
