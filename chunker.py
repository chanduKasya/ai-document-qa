
from pathlib import Path
import re


PROJECT_ROOT = Path(__file__).parent
INPUT_PATH = PROJECT_ROOT / "data" / "extracted_text.txt"
OUTPUT_PATH = PROJECT_ROOT/ "data" / "chunks.txt"

CHUNK_SIZE = 100
OVERLAP = 20

def split_into_chunks(text, chunk_size, overlap):
    words = text.split()
    chunks = []
    step = chunk_size - overlap

    for start in range (0, len(words), step):
        chunk_words = words[start:start+chunk_size]
        chunks.append(" ".join(chunk_words))
        if start + chunk_size >= len(words):
            break

    return chunks

def main() -> None:
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Missing {INPUT_PATH} . Run extract_pdf.py first.")


    text = INPUT_PATH.read_text(encoding="utf-8")
    text_without_labels = re.sub(r"\[Page \d+\]", "", text).strip()
    if not text_without_labels:
        raise ValueError("No texxt was found. Use a text-based PDF and rerun extraction.")

    chunks = split_into_chunks(text, CHUNK_SIZE, OVERLAP)

    print(f"Setting: chunk size {CHUNK_SIZE}, overlap {OVERLAP}")
    print(f"Total words: {len(text.split())}")
    print(f"Chunk count: {len(chunks)}")
    print("\n--- First Chunk ---")
    print(chunks[0])
    print("\n--- second chunk (If available) ---")
    print(chunks[1] if len(chunks) > 1 else "Only one chunk was created.")

    output_text = "\n\n".join(
        f"==== CHUNK {i} | {len(chunk.split())} words ====\n{chunk}"
        for i, chunk in enumerate(chunks, start=1)

    )

    OUTPUT_PATH.write_text(output_text, encoding="utf-8")
    print(f"\n Saved chunks to: {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
          
                    


    
    




