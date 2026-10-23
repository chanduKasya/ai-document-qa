from pathlib import Path
import pymupdf


PROJECT_ROOT = Path(__file__).parent
PDF_PATH = PROJECT_ROOT /"data"/ "sample.pdf"
OUTPUT_PATH = PROJECT_ROOT / "data" / "extracted_text.txt"

def extract_text_from_pdf(pdf_path: Path) -> list[dict]:
    pages = []
    with pymupdf.open(pdf_path) as pdf:
        for page_number in range(pdf.page_count):
            page = pdf[page_number]
            text = page.get_text("text")
            pages.append({"page_number": page_number, "text": text})

    return pages


def main() -> None:
    if not PDF_PATH.exists():
        raise FileNotFoundError(f"Missing PDF file: {PDF_PATH}")

    pages = extract_text_from_pdf(PDF_PATH)
    full_text = "\n\n".join(
        f"[Page {page['page_number'] + 1}]\n{page['text']}"
        for page in pages
    )
    OUTPUT_PATH.write_text(full_text, encoding="utf-8")

    text_characters = len(full_text)
    empty_pages = [p["page_number"] for p in pages if not p["text"].strip()]

    print(f"PDF: {PDF_PATH}")
    print(f"Pages Found: {len(pages)}")
    print(f"Output: {OUTPUT_PATH}")
    print(f"Total characters extracted: {text_characters}")
    print(f"Empty pages: {empty_pages}")
    print("Text Preview------------------")
    print(full_text[:500])


if __name__ == "__main__":
        main()








    











       
    

