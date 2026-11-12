# Container for Hugging Face Spaces (Docker SDK). Also works on any Docker host.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Spaces runs containers as user ID 1000, so create that user and work as it.
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    HF_HOME=/home/user/.cache/huggingface
WORKDIR $HOME/app

# CPU-only PyTorch is far smaller than the default GPU build, and this server has no GPU.
RUN pip install --user torch --index-url https://download.pytorch.org/whl/cpu

COPY --chown=user requirements.txt .
RUN pip install --user -r requirements.txt

# Download the embedding model while building the image, so the app starts quickly.
# (Keep this name in sync with EMBEDDING_MODEL in docqa/config.py.)
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

COPY --chown=user docqa ./docqa
COPY --chown=user static ./static

EXPOSE 7860

# Lets Docker report whether the app is up ("healthy" in `docker ps`).
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:' + os.getenv('PORT', '7860') + '/api/health')"

# One worker only: uploaded documents live in this process's memory.
CMD ["sh", "-c", "uvicorn docqa.main:app --host 0.0.0.0 --port ${PORT:-7860}"]
