"""Minimal CLI demo: generate and (optionally) score a single reply.

Run:  python -m scripts.demo
      python -m scripts.demo --email "Can we reschedule our call to Friday?"
"""

from __future__ import annotations

import argparse

from src.config import INDEX_DIR, settings
from src.dataset.load_dataset import load_test, load_train
from src.evaluation.evaluator import Evaluator
from src.generation.reply_generator import ReplyGenerator
from src.retrieval.embedder import Embedder
from src.retrieval.vector_store import VectorStore


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", type=str, default="", help="incoming email text (defaults to a test sample)")
    args = parser.parse_args()

    embedder = Embedder()
    store = VectorStore(embedder)
    try:
        store.load(INDEX_DIR)
    except Exception:
        store.build(load_train())

    generator = ReplyGenerator(store)

    sample = None
    if args.email:
        incoming = args.email
    else:
        sample = load_test()[0]
        incoming = sample.incoming_email

    print(f"Provider: {generator.llm.provider} | model: {generator.llm.model} | embedding: {embedder.backend}\n")
    print("INCOMING EMAIL")
    print("-" * 60)
    print(incoming)

    gen = generator.generate(incoming, exclude_id=sample.id if sample else None)
    print("\nSUGGESTED REPLY")
    print("-" * 60)
    print(gen.generated_reply)

    print("\nRETRIEVED CONTEXT")
    print("-" * 60)
    for r in gen.retrieved_examples:
        print(f"  {r.id} | {r.category} | sim={r.score:.2f}")

    if sample is not None:
        result = Evaluator(embedder=embedder).evaluate_generation(sample, gen)
        print("\nEVALUATION")
        print("-" * 60)
        m = result.metrics
        print(f"  final_score            : {result.final_score:.3f} ({'PASS' if result.passed else 'FAIL'})")
        print(f"  semantic_similarity    : {m.semantic_similarity:.3f}")
        print(f"  required_fact_coverage : {m.required_fact_coverage:.3f}")
        print(f"  intent_alignment       : {m.intent_alignment:.3f}")
        print(f"  tone_match             : {m.tone_match:.3f}")
        print(f"  helpfulness            : {m.helpfulness:.3f}")
        print(f"  safety_no_hallucination: {m.safety_no_hallucination:.3f}")
        print(f"  must_not_include_viol. : {m.must_not_include_violation:.3f}")
        print(f"\n  {result.explanation}")


if __name__ == "__main__":
    main()
