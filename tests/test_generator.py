"""End-to-end tests for the RAG generator and evaluator in mock mode."""

from __future__ import annotations

from src.evaluation.evaluator import Evaluator
from src.generation.reply_generator import ReplyGenerator
from src.retrieval.embedder import Embedder
from src.retrieval.vector_store import VectorStore
from src.schemas import Category, EmailExample, RiskLevel


def _dataset():
    return [
        EmailExample(
            id="s1",
            category=Category.SCHEDULING,
            intent="propose_meeting_time",
            tone="friendly-professional",
            incoming_email="Could we meet this week to discuss the roadmap?",
            gold_reply="Hi, Monday at 10:30 AM ET works. I'll send a calendar invite. Best.",
            required_facts=["Monday at 10:30 AM ET", "calendar invite"],
            must_include=["Monday", "invite"],
            must_not_include=["I am unavailable"],
            ideal_action="Confirm a time and send an invite.",
            risk_level=RiskLevel.LOW,
        ),
        EmailExample(
            id="s2",
            category=Category.SALES_DEMO,
            intent="book_demo",
            tone="enthusiastic-professional",
            incoming_email="We'd like a demo of the dashboard for our team of 40.",
            gold_reply="Hi, happy to run a 30-minute demo. Would Tuesday at 2pm work? Best.",
            required_facts=["30-minute demo"],
            must_include=["demo"],
            must_not_include=["free forever"],
            ideal_action="Offer a demo slot.",
            risk_level=RiskLevel.LOW,
        ),
    ]


def test_generate_returns_reply_and_context():
    store = VectorStore(Embedder()).build(_dataset())
    gen = ReplyGenerator(store).generate("Can we find time this week to talk about the roadmap?")
    # Provider-agnostic invariants: a reply is produced and grounded in retrieval,
    # whether the backend is a real LLM or the offline mock.
    assert gen.generated_reply.strip()
    assert len(gen.retrieved_examples) >= 1
    assert isinstance(gen.used_mock, bool)


def test_evaluator_scores_and_labels():
    data = _dataset()
    store = VectorStore(Embedder()).build(data)
    generator = ReplyGenerator(store)
    evaluator = Evaluator(embedder=store.embedder)

    ex = data[0]
    gen = generator.generate(ex.incoming_email, exclude_id=ex.id)
    result = evaluator.evaluate_generation(ex, gen)

    assert 0.0 <= result.final_score <= 1.0
    assert isinstance(result.passed, bool)
    assert result.explanation
    m = result.metrics
    for value in [
        m.semantic_similarity, m.required_fact_coverage, m.intent_alignment,
        m.tone_match, m.helpfulness, m.safety_no_hallucination,
    ]:
        assert 0.0 <= value <= 1.0


def test_must_not_include_caps_pass():
    data = _dataset()
    store = VectorStore(Embedder()).build(data)
    evaluator = Evaluator(embedder=store.embedder)
    ex = data[0]
    # A reply that violates must_not_include cannot pass regardless of other scores.
    result = evaluator.score_reply(ex, "Hi, I am unavailable this week. Best.")
    assert result.passed is False
