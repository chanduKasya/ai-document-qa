"""Step 1: read the text out of a PDF.

This grew out of extract_pdf.py. It now reads the PDF straight from memory
(no file is written to disk) and checks for problems we can explain to the user.
"""
import unicodedata

import pymupdf


class DocumentError(Exception):
    """A problem with the uploaded file that the user can fix."""


def read_pdf_pages(pdf_bytes, max_pages):
    """Return one dictionary per page: {"page": 1, "text": "..."}."""
    # Real PDFs start with "%PDF-" near the beginning of the file.
    # Checking the content is safer than trusting the file name.
    if b"%PDF-" not in pdf_bytes[:1024]:
        raise DocumentError("This file is not a PDF.")

    try:
        pdf = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    except Exception:
        raise DocumentError("This PDF could not be opened. It may be damaged.")

    with pdf:
        if pdf.needs_pass:
            raise DocumentError("This PDF is password protected. Remove the password and try again.")

        if pdf.page_count > max_pages:
            raise DocumentError(
                "This PDF has " + str(pdf.page_count) + " pages. The limit is "
                + str(max_pages) + " pages."
            )

        pages = []
        for index in range(pdf.page_count):
            text = pdf[index].get_text("text")
            # PDFs often store "fi" or "ffi" as one special character (a ligature).
            # NFKC turns those back into normal letters so search can match them.
            text = unicodedata.normalize("NFKC", text)
            # Page numbers start at 1, the way people count pages.
            pages.append({"page": index + 1, "text": text})

    return pages
