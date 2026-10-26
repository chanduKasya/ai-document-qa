from pathlib import Path
from sentence_transformers import SentenceTransformer
import faiss


TOP_K = 3
PROJECT_ROOT = Path(__file__).parent
CHUNKS_PATH = PROJECT_ROOT / "data" / "chunks.txt"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
CHUNK_MARKER = "===== CHUNK"


def load_chunks(path):
    raw_text = path.read_text(encoding="utf-8").strip()
    parts = raw_text.split(CHUNK_MARKER)

    chunks = []
    for part in parts[1:]:
        lines = part.split("\n", 1)
        if len(lines) == 2:
            content = lines[1].strip()
            if content != "":
                chunks.append(content)
    return chunks



def main() -> None:
    chunks = load_chunks(CHUNKS_PATH)
    print("Chunks loaded:", len(chunks))


    print("Loading the model...")
    model = SentenceTransformer(MODEL_NAME)


    vectors = model.encode(chunks, normalize_embeddings=True)
    vectors = vectors.astype("float32")

    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)

    while True:
        question = input("\n Ask a question (press Enter to quit):").strip()
        if question == "":
            break

        question_vector = model.encode([question], normalize_embeddings=True)
        question_vector = question_vector.astype("float32")

        how_many = min(TOP_K, len(chunks))
        scores, ids = index.search(question_vector, how_many)


        print("\n--- Most relevant chunks ---")
        for i in range(how_many):
            chunk_id = int(ids[0][i])
            score = float(scores[0][i])
            print("\nResult" , i + 1, "| chunk", chunk_id + 1, "| score:", round(score, 3))
            print(chunks[chunk_id])
            


if __name__ == "__main__":
    main()



