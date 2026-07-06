"""Aggregate per-reply results into a system-level report (JSON + Markdown)."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

from src.config import OUTPUT_DIR, settings
from src.schemas import CategoryScore, EvaluationReport, EvaluationResult


def _common_failures(results: List[EvaluationResult]) -> Dict[str, int]:
    """Tally why failing replies failed, using per-metric thresholds."""
    tallies: Dict[str, int] = defaultdict(int)
    for r in results:
        if r.passed:
            continue
        m = r.metrics
        if m.must_not_include_violation > 0:
            tallies["must_not_include_violation"] += 1
        if m.required_fact_coverage < 0.7:
            tallies["missing_required_facts"] += 1
        if m.safety_no_hallucination < 0.9:
            tallies["possible_hallucination"] += 1
        if m.tone_match < 0.6:
            tallies["tone_mismatch"] += 1
        if m.intent_alignment < 0.5:
            tallies["intent_drift"] += 1
        if m.helpfulness < 0.6:
            tallies["low_helpfulness"] += 1
        if m.semantic_similarity < 0.5:
            tallies["low_semantic_similarity"] += 1
    return dict(sorted(tallies.items(), key=lambda kv: -kv[1]))


def build_report(results: List[EvaluationResult]) -> EvaluationReport:
    n = len(results)
    avg = sum(r.final_score for r in results) / n if n else 0.0
    pass_rate = sum(1 for r in results if r.passed) / n if n else 0.0

    by_cat: Dict[str, List[EvaluationResult]] = defaultdict(list)
    for r in results:
        by_cat[r.category].append(r)

    cat_scores: List[CategoryScore] = []
    for cat, items in sorted(by_cat.items()):
        cat_scores.append(
            CategoryScore(
                category=cat,
                count=len(items),
                average_score=round(sum(i.final_score for i in items) / len(items), 4),
                pass_rate=round(sum(1 for i in items if i.passed) / len(items), 4),
            )
        )

    ranked = sorted(results, key=lambda r: r.final_score)
    worst = ranked[:5]
    best = list(reversed(ranked[-5:]))

    return EvaluationReport(
        num_examples=n,
        average_score=round(avg, 4),
        pass_rate=round(pass_rate, 4),
        pass_threshold=settings.pass_threshold,
        category_scores=cat_scores,
        best_examples=best,
        worst_examples=worst,
        common_failure_types=_common_failures(results),
        results=results,
    )


def save_json(report: EvaluationReport, path: Path | str = OUTPUT_DIR / "evaluation_report.json") -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
    return path


def _truncate(text: str, n: int = 240) -> str:
    text = " ".join(text.split())
    return text if len(text) <= n else text[:n] + "…"


def to_markdown(report: EvaluationReport) -> str:
    lines: List[str] = []
    lines.append("# ReplyWise AI — Evaluation Report\n")
    lines.append(f"- **Examples evaluated:** {report.num_examples}")
    lines.append(f"- **Average final score:** {report.average_score:.3f} / 1.00")
    lines.append(f"- **Pass rate:** {report.pass_rate:.1%} (threshold {report.pass_threshold:.2f})\n")

    lines.append("## Score by category\n")
    lines.append("| Category | Count | Avg score | Pass rate |")
    lines.append("|---|---:|---:|---:|")
    for c in report.category_scores:
        lines.append(f"| {c.category} | {c.count} | {c.average_score:.3f} | {c.pass_rate:.0%} |")
    lines.append("")

    lines.append("## Common failure types\n")
    if report.common_failure_types:
        for name, count in report.common_failure_types.items():
            lines.append(f"- **{name.replace('_', ' ')}**: {count}")
    else:
        lines.append("- None — all evaluated replies passed.")
    lines.append("")

    def _block(title: str, items: List[EvaluationResult]) -> None:
        lines.append(f"## {title}\n")
        for r in items:
            lines.append(f"### `{r.id}` — {r.category} — score {r.final_score:.3f} ({'PASS' if r.passed else 'FAIL'})")
            lines.append(f"- **Incoming:** {_truncate(r.incoming_email)}")
            lines.append(f"- **Generated:** {_truncate(r.generated_reply)}")
            lines.append(f"- **Why:** {r.explanation}")
            m = r.metrics
            lines.append(
                "- **Metrics:** "
                f"sim={m.semantic_similarity:.2f}, facts={m.required_fact_coverage:.2f}, "
                f"intent={m.intent_alignment:.2f}, tone={m.tone_match:.2f}, "
                f"help={m.helpfulness:.2f}, safety={m.safety_no_hallucination:.2f}, "
                f"mni_violation={m.must_not_include_violation:.2f}"
            )
            lines.append("")

    _block("Best examples", report.best_examples)
    _block("Worst examples", report.worst_examples)
    return "\n".join(lines)


def save_markdown(report: EvaluationReport, path: Path | str = OUTPUT_DIR / "evaluation_report.md") -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(to_markdown(report), encoding="utf-8")
    return path
