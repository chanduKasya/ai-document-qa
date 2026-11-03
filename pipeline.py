from extract_pdf import extract_text_from_pdf
from chunker import split_into_chunks
from answer_question import build_index

CHUNK_SIZE = 100
OVERLAP = 20


def build_from_pdf(pdf_path):
    pages = extract_text_from_pdf(pdf_path)

    full_text = ""
    for page in pages:
        full_text = full_text + page["text"] + "\n"

    if full_text.strip() == "":
        raise ValueError("No text found. the PDF may be scanned images.")


    chunks = split_into_chunks(full_text, CHUNK_SIZE, OVERLAP)
    model , index = build_index(chunks)

    return pages, chunks , model, index