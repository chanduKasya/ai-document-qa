from pathlib import Path

import pymupdf
import pytest

from conftest import make_pdf
from docqa.pdf_reader import DocumentError, read_pdf_pages


def test_pages_are_numbered_from_one():
    pages = read_pdf_pages(make_pdf(["First page text", "Second page text"]), max_pages=10)
    assert [page["page"] for page in pages] == [1, 2]
    assert "Second page text" in pages[1]["text"]


def test_ligatures_become_normal_letters():
    # The sample handbook stores "ffi" and "fi" as single ligature characters.
    sample = Path(__file__).resolve().parent.parent / "static" / "sample-handbook.pdf"
    pages = read_pdf_pages(sample.read_bytes(), max_pages=10)
    first_page = pages[0]["text"]
    assert "offices" in first_page
    assert "ﬃ" not in first_page  # the "ffi" ligature character


def test_rejects_files_that_are_not_pdfs():
    with pytest.raises(DocumentError, match="not a PDF"):
        read_pdf_pages(b"hello, I am a text file", max_pages=10)


def test_rejects_too_many_pages():
    with pytest.raises(DocumentError, match="limit is 2"):
        read_pdf_pages(make_pdf(["a", "b", "c"]), max_pages=2)


def test_rejects_password_protected_pdfs():
    pdf = pymupdf.open()
    pdf.new_page().insert_text((72, 72), "secret")
    data = pdf.tobytes(encryption=pymupdf.PDF_ENCRYPT_AES_256, user_pw="pw", owner_pw="owner")
    with pytest.raises(DocumentError, match="password"):
        read_pdf_pages(data, max_pages=10)
