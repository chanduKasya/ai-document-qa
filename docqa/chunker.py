"""Step 2: cut the text into small overlapping chunks.

split_into_chunks is the function from chunker.py. chunk_pages is new:
it chunks each page separately, so every chunk remembers its page number.
That page number is what lets answers say "page 4".
"""


def split_into_chunks(text, chunk_size, overlap):
    """Split text into word chunks. Neighbouring chunks share `overlap` words."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero.")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be at least 0 and smaller than chunk_size.")

    words = text.split()
    chunks = []
    step = chunk_size - overlap

    for start in range(0, len(words), step):
        chunk_words = words[start:start + chunk_size]
        chunks.append(" ".join(chunk_words))
        if start + chunk_size >= len(words):
            break

    return chunks


def chunk_pages(pages, chunk_size, overlap):
    """Return a list of chunks: {"id": 1, "page": 3, "text": "..."}."""
    chunks = []
    for page in pages:
        page_chunks = split_into_chunks(page["text"], chunk_size, overlap)
        for text in page_chunks:
            chunk = {"id": len(chunks) + 1, "page": page["page"], "text": text}
            chunks.append(chunk)
    return chunks
