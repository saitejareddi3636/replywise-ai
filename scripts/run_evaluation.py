"""End-to-end evaluation: generate a reply for every test email and score it.

For each held-out test email we retrieve from the *training* index (excluding
the item itself), generate a reply, and score it against its gold labels. The
aggregate report is written to outputs/ as both JSON and Markdown.

Run:  python -m scripts.run_evaluation --limit 40
"""

from __future__ import annotations

import argparse
import time

from src.config import INDEX_DIR, settings
from src.dataset.load_dataset import load_test, load_train
from src.evaluation.evaluator import Evaluator
from src.evaluation.report import build_report, save_json, save_markdown
from src.generation.reply_generator import ReplyGenerator
from src.retrieval.embedder import Embedder
from src.retrieval.vector_store import VectorStore


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the ReplyWise evaluation harness.")
    parser.add_argument("--limit", type=int, default=0, help="evaluate only the first N test emails (0 = all)")
    args = parser.parse_args()

    embedder = Embedder()
    store = VectorStore(embedder)
    try:
        store.load(INDEX_DIR)
    except Exception:
        store.build(load_train())

    generator = ReplyGenerator(store)
    evaluator = Evaluator(embedder=embedder)

    test = load_test()
    if args.limit:
        test = test[: args.limit]

    print(f"Provider={generator.llm.provider}  model={generator.llm.model}  "
          f"embed_backend={embedder.backend}  test_examples={len(test)}")
    print("Running generation + evaluation...\n")

    results = []
    t0 = time.time()
    for i, ex in enumerate(test, 1):
        gen = generator.generate(ex.incoming_email, exclude_id=ex.id)
        result = evaluator.evaluate_generation(ex, gen)
        results.append(result)
        print(f"[{i:>3}/{len(test)}] {ex.id} {ex.category.value:20s} score={result.final_score:.3f} "
              f"{'PASS' if result.passed else 'FAIL'}")

    report = build_report(results)
    json_path = save_json(report)
    md_path = save_markdown(report)

    dt = time.time() - t0
    print("\n" + "=" * 60)
    print(f"Average score : {report.average_score:.3f}")
    print(f"Pass rate     : {report.pass_rate:.1%} (threshold {report.pass_threshold:.2f})")
    print(f"Elapsed       : {dt:.1f}s")
    print("\nPer-category:")
    for c in report.category_scores:
        print(f"  {c.category:22s} n={c.count:<3} avg={c.average_score:.3f} pass={c.pass_rate:.0%}")
    if report.common_failure_types:
        print("\nCommon failure types:")
        for name, count in report.common_failure_types.items():
            print(f"  {name:28s} {count}")
    print(f"\nWrote {json_path}\nWrote {md_path}")


if __name__ == "__main__":
    main()
