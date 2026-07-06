"""Unit tests for the evaluation metrics.

These lock in the *intended behavior* of each metric: coverage rewards present
facts and forgives paraphrase, must-not-include is caught, and the
hallucination check flags ungrounded specifics. They run offline (hash embedder
fallback is fine).
"""

from __future__ import annotations

from src.evaluation import metrics as M
from src.retrieval.embedder import Embedder
from src.schemas import Category, EmailExample, RiskLevel

EMB = Embedder()


def _example(**kw) -> EmailExample:
    base = dict(
        id="t",
        category=Category.SCHEDULING,
        intent="propose_meeting_time",
        tone="friendly-professional",
        incoming_email="Can we meet this week to discuss the roadmap?",
        gold_reply="Hi, Monday at 10:30 AM works. I'll send a calendar invite. Best.",
        required_facts=["Monday at 10:30 AM", "calendar invite"],
        must_include=["Monday", "invite"],
        must_not_include=["I am unavailable"],
        ideal_action="Confirm a time and send an invite.",
        risk_level=RiskLevel.LOW,
    )
    base.update(kw)
    return EmailExample(**base)


def test_coverage_full_and_empty():
    assert M.coverage_score([], "anything") == 1.0
    assert M.coverage_score(["invoice INV-1234"], "Your invoice INV-1234 is corrected.") == 1.0


def test_coverage_allows_paraphrase():
    # 70% token overlap threshold should still credit a lightly reworded fact.
    assert M._covered("send a calendar invite", "I'll send you a calendar invite shortly.")


def test_coverage_penalizes_missing():
    score = M.coverage_score(["Monday at 10:30 AM", "calendar invite"], "Sounds good, talk soon.")
    assert score < 0.5


def test_must_not_include_violation():
    assert M.violation_score(["I am unavailable"], "Sorry, I am unavailable this week.") == 1.0
    assert M.violation_score(["I am unavailable"], "Happy to meet Monday.") == 0.0


def test_semantic_similarity_bounds():
    s = M.semantic_similarity("Let's meet Monday", "We can meet on Monday", EMB)
    assert 0.0 <= s <= 1.0


def test_tone_penalizes_rudeness():
    ex_tone = "empathetic-professional"
    polite = M.tone_match("Hi, I'm sorry for the trouble. Thanks for your patience. Best.", ex_tone)
    rude = M.tone_match("Calm down, it's not a big deal.", ex_tone)
    assert polite > rude


def test_safety_flags_ungrounded_specifics():
    ex = _example(incoming_email="Can we meet this week?", required_facts=[])
    # Reply invents a ticket number and a price not present anywhere in the input.
    bad = M.safety_no_hallucination("Your ticket #99999 is fixed and it costs $4,200.", ex, retrieved=[])
    assert bad < 1.0


def test_safety_grounded_specifics_pass():
    ex = _example(
        incoming_email="Invoice INV-1234 for $5,000 looks wrong.",
        required_facts=["INV-1234", "$5,000"],
    )
    good = M.safety_no_hallucination("Invoice INV-1234 corrected; total remains $5,000.", ex, retrieved=[])
    assert good == 1.0


def test_helpfulness_rewards_structure():
    ex = _example()
    strong = M.helpfulness(
        "Hi, Monday at 10:30 AM works and I'll send a calendar invite. Let me know if that suits. Best.", ex
    )
    weak = M.helpfulness("ok", ex)
    assert strong > weak
