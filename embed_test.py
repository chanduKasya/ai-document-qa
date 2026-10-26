from sentence_transformers import SentenceTransformer
import numpy as np


model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

sentences = [
    "A router sends data between networks",
    "Routers forward packets",
    "I like eating mangoes",

]

vectors = model.encode(sentences, normalize_embeddings = True)

print("Shape:", vectors.shape)
print("First 5 numbers of sentence 1:", vectors[0][:5])

print("Sentence 1 vs 2:", np.dot(vectors[0], vectors[1]))
print("Sentence 1 vs 3:", np.dot(vectors[0], vectors[2])
      )