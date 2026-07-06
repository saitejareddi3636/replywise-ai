"""Reference-based and reference-free metrics for a generated reply.

Design philosophy: a good reply is not the one that copies the gold text word
for word — it is the one that (a) carries the required facts, (b) pursues the
right intent, (c) hits the right tone, (d) is genuinely helpful, and (e) does
not invent details. Exact match punishes valid paraphrases and rewards nothing
about safety, so we deliberately combine several complementary signals, each in
[0, 1], and weight them into a final score elsewhere (`evaluator.py`).

All metrics here are dependency-light and deterministic. `semantic_similarity`
and `intent_alignment` use the shared embedder; everything else is lexical or
rule-based so the scoring is transparent and debuggable.
"""

from __future__ import annotations

import re
from typing import List, Optional

import numpy as np

from src.retrieval.embedder import Embedder
from src.schemas import EmailExample, RetrievedExample

_STOPWORDS = {
    "the", "a", "an", "and", "or", "to", "of", "in", "on", "at", "for", "is",
    "are", "be", "with", "your", "you", "i", "we", "our", "it", "this", "that",
    "will", "can", "by", "as", "if", "so", "please", "hi", "hello", "thanks",
}


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def _sig_tokens(text: str) -> List[str]:
    toks = re.findall(r"[a-z0-9$%:./-]+", text.lower())
    return [t for t in toks if len(t) > 1 and t not in _STOPWORDS]


def _covered(item: str, text: str) -> bool:
    """Is `item` (a fact or phrase) present in `text`, allowing paraphrase?

    True if the exact normalized phrase appears, or if at least 70% of the
    item's significant tokens appear in the text (order-independent). This is
    forgiving enough to credit a reworded fact but strict enough to catch a
    dropped one.
    """
    n_item, n_text = _normalize(item), _normalize(text)
    if n_item and n_item in n_text:
        return True
    item_toks = _sig_tokens(item)
    if not item_toks:
        return False
    text_toks = set(_sig_tokens(text))
    hits = sum(1 for t in item_toks if t in text_toks)
    return (hits / len(item_toks)) >= 0.7


def coverage_score(items: List[str], text: str) -> float:
    if not items:
        return 1.0  # nothing required => trivially satisfied
    return sum(1 for it in items if _covered(it, text)) / len(items)


def violation_score(items: List[str], text: str) -> float:
    """Fraction of forbidden items that appear. 0 is clean, 1 is worst."""
    if not items:
        return 0.0
    return sum(1 for it in items if _covered(it, text)) / len(items)


def semantic_similarity(generated: str, gold: str, embedder: Embedder) -> float:
    vecs = embedder.encode([generated, gold])
    sim = float(np.dot(vecs[0], vecs[1]))  # vectors are L2-normalized
    return max(0.0, min(1.0, (sim + 1.0) / 2.0 if sim < 0 else sim))


def intent_alignment(generated: str, example: EmailExample, embedder: Embedder) -> float:
    """How well the reply pursues the intended action.

    We embed the reply and compare it to a short intent description built from
    the labels (`intent` + `ideal_action`). A reply that chases the right goal
    lands close to that description regardless of exact wording.
    """
    intent_desc = f"{example.intent.replace('_', ' ')}. {example.ideal_action}"
    vecs = embedder.encode([generated, intent_desc])
    sim = float(np.dot(vecs[0], vecs[1]))
    # Rescale: intent descriptions are terse, so raw cosine tops out lower than
    # reply-to-reply similarity. Map [0.1, 0.6] -> [0, 1] and clip.
    return max(0.0, min(1.0, (sim - 0.1) / 0.5))


# --- tone -----------------------------------------------------------------

_TONE_LEXICON = {
    "empathetic": ["sorry", "understand", "apolog", "frustrat", "appreciate", "hear you"],
    "apologetic": ["sorry", "apolog", "apologies", "regret"],
    "warm": ["thanks", "glad", "great to", "happy to", "welcome", "pleasure"],
    "friendly": ["happy to", "glad", "sure", "of course", "let me know"],
    "enthusiastic": ["great", "love", "excited", "glad", "look forward"],
    "professional": ["best", "regards", "please", "confirm", "follow up"],
    "precise": ["corrected", "confirm", "attached", "terms", "total", "specifically"],
    "accountable": ["i'll", "i will", "own", "personally", "ensure", "make sure"],
    "diplomatic": ["explore", "perhaps", "worth", "open to", "would help", "consider"],
    "courteous": ["thanks", "appreciate", "apologies", "kindly", "no problem"],
    "organized": ["confirm", "plan", "agenda", "schedule", "by", "details"],
    "concise": [],  # handled via length heuristic
}

_RUDE_MARKERS = ["calm down", "not my problem", "you should have", "obviously", "as i said", "whatever"]


def tone_match(generated: str, expected_tone: str) -> float:
    text = generated.lower()
    traits = [t for t in re.split(r"[-\s]+", expected_tone.lower()) if t]
    if not traits:
        traits = ["professional"]

    hits, checked = 0, 0
    for trait in traits:
        markers = _TONE_LEXICON.get(trait)
        if markers is None:
            continue
        checked += 1
        if not markers:  # e.g. "concise": reward brevity
            hits += 1 if len(generated.split()) <= 120 else 0
            continue
        if any(m in text for m in markers):
            hits += 1
    base = (hits / checked) if checked else 0.6

    # Politeness backbone every professional reply should have.
    if any(w in text for w in ["thanks", "thank you", "please", "best", "regards", "appreciate"]):
        base = min(1.0, base + 0.15)
    # Hard penalty for rude phrasing.
    if any(m in text for m in _RUDE_MARKERS):
        base *= 0.4
    return max(0.0, min(1.0, base))


# --- helpfulness ----------------------------------------------------------

_ACTION_MARKERS = [
    "i'll", "i will", "let me know", "could you", "please", "attached", "next step",
    "follow up", "confirm", "send", "schedule", "share", "update you", "?",
]


def helpfulness(generated: str, example: EmailExample) -> float:
    """Completeness proxy: structure + a concrete next step + fact coverage."""
    text = generated.lower()
    words = generated.split()

    has_greeting = bool(re.match(r"(hi|hello|dear|hey)\b", text))
    has_signoff = any(s in text for s in ["best", "regards", "sincerely", "thanks,", "cheers"])
    has_action = any(m in text for m in _ACTION_MARKERS)
    good_length = 25 <= len(words) <= 180
    facts = coverage_score(example.required_facts, generated)

    score = (
        0.15 * has_greeting
        + 0.15 * has_signoff
        + 0.25 * has_action
        + 0.15 * good_length
        + 0.30 * facts
    )
    return max(0.0, min(1.0, score))


# --- hallucination / safety ----------------------------------------------

_SPECIFIC_PATTERNS = [
    r"\$[\d,]+(?:\.\d+)?",          # money
    r"#\d{3,}",                      # ticket numbers
    r"\bINV-\d+\b",                 # invoice ids
    r"\bPO-?\d+\b",                 # purchase orders
    r"\b\d{1,2}:\d{2}\s?(?:am|pm)?\b",  # times
    r"\b\d{1,3}%\b",                # percentages
]


def _grounding_text(example: EmailExample, retrieved: Optional[List[RetrievedExample]]) -> str:
    parts = [example.incoming_email, " ".join(example.required_facts), " ".join(example.must_include)]
    if retrieved:
        for r in retrieved:
            parts.append(r.incoming_email)
            parts.append(r.gold_reply)
    return _normalize(" ".join(parts))


def safety_no_hallucination(
    generated: str,
    example: EmailExample,
    retrieved: Optional[List[RetrievedExample]] = None,
) -> float:
    """1.0 = every concrete specific in the reply is grounded in the input.

    We extract high-risk specifics (amounts, ticket/invoice numbers, times,
    percentages) from the generated reply and check each one is present in the
    grounding text (the incoming email, the required facts, or the retrieved
    exemplars). An ungrounded specific is a likely fabrication.
    """
    grounding = _grounding_text(example, retrieved)
    specifics: List[str] = []
    for pat in _SPECIFIC_PATTERNS:
        specifics.extend(m.group(0) for m in re.finditer(pat, generated, flags=re.IGNORECASE))
    if not specifics:
        return 1.0  # no concrete claims to fabricate
    grounded = sum(1 for s in specifics if _normalize(s) in grounding)
    return grounded / len(specifics)
