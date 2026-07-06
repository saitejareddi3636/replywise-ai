"""Vector store over the training email/reply pairs.

Uses FAISS (inner-product on normalized vectors = cosine similarity) when it is
installed; otherwise falls back to an exact NumPy cosine search. At the dataset
sizes here (~200 vectors) both are effectively instant, so the fallback costs
nothing in practice and removes a hard dependency.
"""

from __future__ import annotations

import json
import pickle
from pathlib import Path
from typing import List, Optional

import numpy as np

from src.config import INDEX_DIR, settings
from src.retrieval.embedder import Embedder
from src.schemas import EmailExample, RetrievedExample


class VectorStore:
    def __init__(self, embedder: Optional[Embedder] = None):
        self.embedder = embedder or Embedder()
        self.examples: List[EmailExample] = []
        self.matrix: Optional[np.ndarray] = None  # (n, dim), L2-normalized
        self._faiss_index = None

    # --- build / persist --------------------------------------------------

    def build(self, examples: List[EmailExample]) -> "VectorStore":
        self.examples = examples
        texts = [ex.incoming_email for ex in examples]
        self.matrix = self.embedder.encode(texts).astype(np.float32)
        self._try_build_faiss()
        return self

    def _try_build_faiss(self) -> None:
        try:
            import faiss

            index = faiss.IndexFlatIP(self.matrix.shape[1])
            index.add(self.matrix)
            self._faiss_index = index
        except Exception:
            self._faiss_index = None

    def save(self, directory: Path | str = INDEX_DIR) -> None:
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        np.save(directory / "matrix.npy", self.matrix)
        with (directory / "examples.jsonl").open("w", encoding="utf-8") as fh:
            for ex in self.examples:
                fh.write(ex.model_dump_json() + "\n")
        meta = {"backend": self.embedder.backend, "dim": int(self.matrix.shape[1])}
        (directory / "meta.json").write_text(json.dumps(meta, indent=2))

    def load(self, directory: Path | str = INDEX_DIR) -> "VectorStore":
        directory = Path(directory)
        self.matrix = np.load(directory / "matrix.npy").astype(np.float32)
        self.examples = []
        with (directory / "examples.jsonl").open("r", encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    self.examples.append(EmailExample.model_validate_json(line))
        self._try_build_faiss()
        return self

    # --- query ------------------------------------------------------------

    def search(self, query: str, top_k: int | None = None, exclude_id: str | None = None) -> List[RetrievedExample]:
        if self.matrix is None or not self.examples:
            raise RuntimeError("vector store is empty; call build() or load() first")
        top_k = top_k or settings.top_k
        q = self.embedder.encode_one(query).astype(np.float32)

        # Over-fetch by one so we can drop a self-match without shrinking results.
        k = min(top_k + 1, len(self.examples))
        if self._faiss_index is not None:
            scores, idxs = self._faiss_index.search(q.reshape(1, -1), k)
            pairs = list(zip(idxs[0].tolist(), scores[0].tolist()))
        else:
            sims = self.matrix @ q
            order = np.argsort(-sims)[:k]
            pairs = [(int(i), float(sims[i])) for i in order]

        results: List[RetrievedExample] = []
        for i, score in pairs:
            ex = self.examples[i]
            if exclude_id is not None and ex.id == exclude_id:
                continue
            results.append(
                RetrievedExample(
                    id=ex.id,
                    category=ex.category.value,
                    intent=ex.intent,
                    tone=ex.tone,
                    incoming_email=ex.incoming_email,
                    gold_reply=ex.gold_reply,
                    score=round(float(score), 4),
                )
            )
            if len(results) >= top_k:
                break
        return results
