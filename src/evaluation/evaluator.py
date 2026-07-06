"""Combine the individual metrics into a single scored, explained verdict."""

from __future__ import annotations

from typing import List, Optional

from src.config import settings
from src.evaluation import metrics as M
from src.evaluation.judge import Judge
from src.retrieval.embedder import Embedder
from src.schemas import (
    EmailExample,
    EvaluationResult,
    GenerationResult,
    MetricBreakdown,
    RetrievedExample,
)


class Evaluator:
    def __init__(self, embedder: Optional[Embedder] = None, judge: Optional[Judge] = None):
        self.embedder = embedder or Embedder()
        self.judge = judge if judge is not None else Judge()

    def score_reply(
        self,
        example: EmailExample,
        generated_reply: str,
        retrieved: Optional[List[RetrievedExample]] = None,
    ) -> EvaluationResult:
        gen = generated_reply

        breakdown = MetricBreakdown(
            semantic_similarity=round(M.semantic_similarity(gen, example.gold_reply, self.embedder), 4),
            required_fact_coverage=round(M.required_fact_coverage(example, gen), 4),
            must_include_coverage=round(M.coverage_score(example.must_include, gen), 4),
            must_not_include_violation=round(M.violation_score(example.must_not_include, gen), 4),
            intent_alignment=round(M.intent_alignment(gen, example, self.embedder), 4),
            tone_match=round(M.tone_match(gen, example.tone), 4),
            helpfulness=round(M.helpfulness(gen, example), 4),
            safety_no_hallucination=round(M.safety_no_hallucination(gen, example, retrieved), 4),
        )

        verdict = self.judge.score(example, gen)
        if verdict is not None:
            breakdown.judge_score = round(verdict.overall, 4)

        final = self._final_score(breakdown)
        passed = final >= settings.pass_threshold and breakdown.must_not_include_violation == 0.0
        explanation = self._explain(example, breakdown, final, passed, verdict.reasoning if verdict else None)

        return EvaluationResult(
            id=example.id,
            category=example.category.value,
            incoming_email=example.incoming_email,
            gold_reply=example.gold_reply,
            generated_reply=gen,
            retrieved_examples=retrieved or [],
            metrics=breakdown,
            final_score=round(final, 4),
            passed=passed,
            explanation=explanation,
        )

    def evaluate_generation(self, example: EmailExample, gen: GenerationResult) -> EvaluationResult:
        return self.score_reply(example, gen.generated_reply, gen.retrieved_examples)

    # --- scoring internals ------------------------------------------------

    def _final_score(self, b: MetricBreakdown) -> float:
        w = settings.weights
        score = (
            w["semantic_similarity"] * b.semantic_similarity
            + w["required_fact_coverage"] * b.required_fact_coverage
            + w["intent_alignment"] * b.intent_alignment
            + w["tone_match"] * b.tone_match
            + w["helpfulness"] * b.helpfulness
            + w["safety_no_hallucination"] * b.safety_no_hallucination
        )
        # Penalty for including forbidden content, scaled by how much leaked.
        score -= settings.must_not_include_penalty * b.must_not_include_violation
        return max(0.0, min(1.0, score))

    def _explain(
        self,
        example: EmailExample,
        b: MetricBreakdown,
        final: float,
        passed: bool,
        judge_reason: Optional[str],
    ) -> str:
        parts: List[str] = []
        parts.append(f"Final score {final:.2f} ({'PASS' if passed else 'FAIL'}, threshold {settings.pass_threshold:.2f}).")

        if b.required_fact_coverage >= 0.99:
            parts.append("All required facts are present.")
        elif b.required_fact_coverage >= 0.5:
            parts.append(f"Partial fact coverage ({b.required_fact_coverage:.0%}) — some required details are missing.")
        else:
            parts.append(f"Poor fact coverage ({b.required_fact_coverage:.0%}); key details are absent.")

        if b.must_not_include_violation > 0:
            parts.append("Contains forbidden/off-limits phrasing (must-not-include violation), which caps the score.")

        if b.safety_no_hallucination < 0.99:
            parts.append(f"Possible ungrounded specifics detected (safety {b.safety_no_hallucination:.0%}).")
        else:
            parts.append("No ungrounded specifics detected.")

        if b.tone_match < 0.6:
            parts.append(f"Tone does not fully match the expected '{example.tone}' register.")
        if b.intent_alignment < 0.5:
            parts.append("Reply drifts from the sender's core intent.")
        if b.helpfulness < 0.6:
            parts.append("Reply lacks a clear next step or structure.")

        if judge_reason:
            parts.append(f"LLM judge: {judge_reason}")
        return " ".join(parts)
