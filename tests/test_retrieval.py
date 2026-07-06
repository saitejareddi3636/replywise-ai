"""Tests for the embedder and vector store."""

from __future__ import annotations

import numpy as np

from src.retrieval.embedder import Embedder
from src.retrieval.vector_store import VectorStore
from src.schemas import Category, EmailExample, RiskLevel


def _mk(id_: str, text: str, reply: str) -> EmailExample:
    return EmailExample(
        id=id_,
        category=Category.SCHEDULING,
        intent="respond",
        tone="professional",
        incoming_email=text,
        gold_reply=reply,
        required_facts=[],
        risk_level=RiskLevel.LOW,
    )


def test_embeddings_are_normalized():
    emb = Embedder()
    vecs = emb.encode(["hello world", "another sentence"])
    norms = np.linalg.norm(vecs, axis=1)
    assert np.allclose(norms, 1.0, atol=1e-3)


def test_search_returns_topk_and_excludes_self():
    examples = [
        _mk("a", "Can we schedule a meeting about the budget?", "Sure, Monday works."),
        _mk("b", "Please reschedule our call to Friday afternoon.", "Friday at 2pm works."),
        _mk("c", "The invoice total looks incorrect.", "I'll review the invoice."),
        _mk("d", "I'd like a product demo for my team.", "Happy to demo Tuesday."),
    ]
    store = VectorStore(Embedder()).build(examples)

    results = store.search("Can we set up a meeting to talk about budget?", top_k=2)
    assert len(results) == 2
    # Most relevant should be the budget-meeting example.
    assert results[0].id == "a"

    # Excluding an id must drop it from results.
    excluded = store.search(examples[0].incoming_email, top_k=3, exclude_id="a")
    assert all(r.id != "a" for r in excluded)


def test_save_and_load_roundtrip(tmp_path):
    examples = [
        _mk("a", "Schedule a meeting please", "Sure."),
        _mk("b", "Demo request for my team", "Happy to help."),
    ]
    store = VectorStore(Embedder()).build(examples)
    store.save(tmp_path)

    loaded = VectorStore(Embedder()).load(tmp_path)
    assert len(loaded.examples) == 2
    assert loaded.matrix.shape == store.matrix.shape
    res = loaded.search("meeting", top_k=1)
    assert len(res) == 1
