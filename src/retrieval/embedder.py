"""Text embedder.

Primary path: sentence-transformers (`all-MiniLM-L6-v2`), a compact, strong
model for short-text semantic similarity. Fallback path: a deterministic
hashing embedding used only when sentence-transformers is unavailable or the
model can't be downloaded (e.g. offline CI). The fallback keeps the whole
pipeline and test suite runnable without network access; it is clearly weaker
and the code logs which path is active.
"""

from __future__ import annotations

import hashlib
from typing import List, Sequence

import numpy as np

from src.config import settings


class Embedder:
    def __init__(self, model_name: str | None = None):
        self.model_name = model_name or settings.embedding_model
        self._model = None
        self._dim = 384  # all-MiniLM-L6-v2 dimensionality; matches the fallback
        self.backend = "hash"
        self._try_load_model()

    def _try_load_model(self) -> None:
        try:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
            # Method was renamed across versions; support both.
            get_dim = getattr(self._model, "get_embedding_dimension", None) or self._model.get_sentence_embedding_dimension
            self._dim = get_dim()
            self.backend = "sentence-transformers"
        except Exception:
            # Stay on the deterministic fallback. This is intentional, not fatal.
            self._model = None
            self.backend = "hash"

    @property
    def dim(self) -> int:
        return self._dim

    def _hash_embed_one(self, text: str) -> np.ndarray:
        """Deterministic bag-of-hashed-tokens embedding, L2-normalized.

        Not competitive with a real model, but stable and dependency-free so
        tests and offline demos still exercise the full retrieval path.
        """
        vec = np.zeros(self._dim, dtype=np.float32)
        tokens = "".join(c.lower() if c.isalnum() else " " for c in text).split()
        for tok in tokens:
            h = int(hashlib.md5(tok.encode()).hexdigest(), 16)
            idx = h % self._dim
            sign = 1.0 if (h >> 8) % 2 == 0 else -1.0
            vec[idx] += sign
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec /= norm
        return vec

    def encode(self, texts: Sequence[str]) -> np.ndarray:
        if isinstance(texts, str):
            texts = [texts]
        if self._model is not None:
            emb = self._model.encode(list(texts), normalize_embeddings=True, show_progress_bar=False)
            return np.asarray(emb, dtype=np.float32)
        return np.vstack([self._hash_embed_one(t) for t in texts])

    def encode_one(self, text: str) -> np.ndarray:
        return self.encode([text])[0]
