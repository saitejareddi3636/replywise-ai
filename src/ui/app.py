"""Streamlit demo UI for ReplyWise AI.

Run:  streamlit run src/ui/app.py

Paste an incoming email, get a suggested reply grounded in retrieved past
examples, and (optionally) score it against a gold reply with the full metric
breakdown. Everything works offline in mock mode if no API key is set.
"""

from __future__ import annotations

import streamlit as st

from src.config import INDEX_DIR, settings
from src.dataset.load_dataset import load_test, load_train
from src.evaluation.evaluator import Evaluator
from src.generation.reply_generator import ReplyGenerator
from src.retrieval.embedder import Embedder
from src.retrieval.vector_store import VectorStore
from src.schemas import EmailExample, RiskLevel


@st.cache_resource(show_spinner="Loading model and index...")
def _load():
    embedder = Embedder()
    store = VectorStore(embedder)
    try:
        store.load(INDEX_DIR)
    except Exception:
        store.build(load_train())
    return store, ReplyGenerator(store), Evaluator(embedder=embedder)


def main() -> None:
    st.set_page_config(page_title="ReplyWise AI", page_icon=None, layout="wide")
    st.title("ReplyWise AI")
    st.caption("Retrieval-grounded suggested email replies, with transparent quality scoring.")

    store, generator, evaluator = _load()

    with st.sidebar:
        st.subheader("System status")
        provider = generator.llm.provider
        st.write(f"LLM provider: `{provider}`")
        st.write(f"Embedding backend: `{store.embedder.backend}`")
        st.write(f"Indexed examples: `{len(store.examples)}`")
        st.write(f"Top-k retrieval: `{settings.top_k}`")
        if provider == "mock":
            st.info("Mock mode: no LLM available, replies use the nearest-neighbor baseline.")

        st.divider()
        st.subheader("Try a sample")
        try:
            samples = load_test()
        except Exception:
            samples = []
        sample = None
        if samples:
            labels = [f"{ex.id} — {ex.category.value}" for ex in samples[:20]]
            pick = st.selectbox("Load a labeled test email", ["(none)"] + labels)
            if pick != "(none)":
                sample = samples[labels.index(pick)]

    default_email = sample.incoming_email if sample else (
        "Hi, we're evaluating your product for our team of about 40 and would love a demo. "
        "Could you also share pricing?"
    )
    incoming = st.text_area("Incoming email", value=default_email, height=180)

    col_a, col_b = st.columns([1, 1])
    with col_a:
        top_k = st.slider("Retrieved examples (k)", 1, 8, settings.top_k)
    with col_b:
        gold = st.text_area(
            "Gold reply (optional — enables scoring)",
            value=sample.gold_reply if sample else "",
            height=100,
        )

    if st.button("Generate suggested reply", type="primary"):
        with st.spinner("Retrieving and generating..."):
            gen = generator.generate(incoming, top_k=top_k)

        st.subheader("Suggested reply")
        st.write(gen.generated_reply)

        with st.expander(f"Retrieved context ({len(gen.retrieved_examples)} examples)"):
            for r in gen.retrieved_examples:
                st.markdown(f"**{r.id}** · {r.category} · similarity {r.score:.2f}")
                st.text(r.incoming_email)
                st.caption("Sent reply:")
                st.text(r.gold_reply)
                st.divider()

        if gold.strip():
            example = sample or EmailExample(
                id="adhoc",
                category="follow_up",
                intent="respond",
                tone="professional",
                incoming_email=incoming,
                gold_reply=gold,
                risk_level=RiskLevel.LOW,
            )
            if sample is None:
                example = example.model_copy(update={"incoming_email": incoming, "gold_reply": gold})
            result = evaluator.evaluate_generation(example, gen)

            st.subheader(f"Evaluation — final score {result.final_score:.2f} ({'PASS' if result.passed else 'FAIL'})")
            m = result.metrics
            cols = st.columns(4)
            cols[0].metric("Semantic sim", f"{m.semantic_similarity:.2f}")
            cols[1].metric("Fact coverage", f"{m.required_fact_coverage:.2f}")
            cols[2].metric("Intent", f"{m.intent_alignment:.2f}")
            cols[3].metric("Tone", f"{m.tone_match:.2f}")
            cols2 = st.columns(4)
            cols2[0].metric("Helpfulness", f"{m.helpfulness:.2f}")
            cols2[1].metric("Safety", f"{m.safety_no_hallucination:.2f}")
            cols2[2].metric("Must-include", f"{m.must_include_coverage:.2f}")
            cols2[3].metric("MNI violation", f"{m.must_not_include_violation:.2f}")
            st.info(result.explanation)


if __name__ == "__main__":
    main()
