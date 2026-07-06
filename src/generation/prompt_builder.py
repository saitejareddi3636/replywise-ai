"""Prompt construction for the RAG reply generator.

The prompt does three jobs: (1) fix the assistant's role and guardrails,
(2) inject the top-k retrieved email/reply pairs as few-shot exemplars so the
model matches the house style and grounds its facts, and (3) instruct it to ask
for clarification rather than invent details it wasn't given.
"""

from __future__ import annotations

from typing import List

from src.schemas import RetrievedExample

SYSTEM_PROMPT = """You are a professional email assistant that drafts suggested replies on behalf of a busy professional.

Rules you must follow:
- Directly address the sender's intent and answer their question.
- Use ONLY facts present in the incoming email or clearly implied by it. Do NOT invent names, prices, dates, ticket numbers, or commitments.
- If a necessary detail is missing, ask a concise clarifying question instead of guessing.
- Match the tone the situation calls for (empathetic for complaints, warm for recruiting, precise for billing).
- Be concise and well-structured. Include a greeting and a sign-off.
- Never be dismissive, never blame the sender, never over-promise.

You will be shown a few examples of past incoming emails and the replies that were sent. Use them as a guide for style and structure, not as facts to copy."""


def _format_examples(examples: List[RetrievedExample]) -> str:
    blocks = []
    for i, ex in enumerate(examples, 1):
        blocks.append(
            f"--- Example {i} (category: {ex.category}, tone: {ex.tone}, similarity: {ex.score:.2f}) ---\n"
            f"INCOMING EMAIL:\n{ex.incoming_email}\n\n"
            f"SENT REPLY:\n{ex.gold_reply}\n"
        )
    return "\n".join(blocks)


def build_user_prompt(incoming_email: str, examples: List[RetrievedExample]) -> str:
    context = _format_examples(examples) if examples else "(no similar past examples found)"
    return (
        "Here are the most similar past email/reply pairs for reference:\n\n"
        f"{context}\n\n"
        "======================================\n"
        "Now draft a suggested reply to this NEW incoming email. "
        "Return only the reply text, no preamble.\n\n"
        f"NEW INCOMING EMAIL:\n{incoming_email}\n"
    )
