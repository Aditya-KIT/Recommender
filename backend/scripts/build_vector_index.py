"""
build_vector_index.py — Placeholder for vector index builder.

Currently the retriever uses TF-IDF (scikit-learn).
This script is reserved for building a FAISS or Chroma vector index
if you want to upgrade to semantic search using sentence embeddings.

Usage (future):
  cd backend
  python scripts/build_vector_index.py

Requirements (future):
  pip install sentence-transformers faiss-cpu

Steps to upgrade:
  1. Load shl_catalog.json
  2. Encode each catalog document with a sentence transformer
  3. Build a FAISS flat index
  4. Save to backend/data/vector_index.faiss
  5. Update retriever.py to load and query the FAISS index
"""
import json
from pathlib import Path

CATALOG_PATH = Path(__file__).resolve().parents[1] / "data" / "shl_catalog.json"


def load_catalog():
    with CATALOG_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def item_to_document(item: dict) -> str:
    parts = [
        item.get("name", ""),
        item.get("test_type", ""),
        item.get("description", ""),
        " ".join(item.get("skills", [])),
        " ".join(item.get("job_family", [])),
        item.get("duration", ""),
    ]
    return " ".join(str(p) for p in parts if p)


def build_tfidf_preview():
    """
    Preview TF-IDF document count — useful to verify catalog is loaded correctly.
    Run this now to confirm the catalog is indexed properly.
    """
    from sklearn.feature_extraction.text import TfidfVectorizer

    catalog = load_catalog()
    documents = [item_to_document(item) for item in catalog]

    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    matrix = vectorizer.fit_transform(documents)

    print(f"Catalog items   : {len(catalog)}")
    print(f"TF-IDF shape    : {matrix.shape}")
    print(f"Vocabulary size : {len(vectorizer.vocabulary_)}")
    print("\nSample catalog items:")
    for item in catalog[:3]:
        print(f"  - {item['name']} ({item['test_type']})")


if __name__ == "__main__":
    build_tfidf_preview()
    print(
        "\nTo upgrade to semantic search, integrate sentence-transformers + FAISS here."
        "\nSee comments at the top of this file for instructions."
    )
