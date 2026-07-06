"""Build and persist the retrieval index from the training dataset.

Run:  python -m scripts.build_index
"""

from __future__ import annotations

from src.config import INDEX_DIR
from src.dataset.load_dataset import load_train
from src.retrieval.embedder import Embedder
from src.retrieval.vector_store import VectorStore


def main() -> None:
    examples = load_train()
    embedder = Embedder()
    print(f"Embedding {len(examples)} examples with backend='{embedder.backend}'...")
    store = VectorStore(embedder).build(examples)
    store.save(INDEX_DIR)
    print(f"Saved index ({len(examples)} vectors, dim={store.matrix.shape[1]}) -> {INDEX_DIR}")


if __name__ == "__main__":
    main()
