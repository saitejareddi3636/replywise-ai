"""The RAG reply pipeline: retrieve -> build prompt -> generate."""

from __future__ import annotations

from typing import List, Optional

from src.config import settings
from src.generation.llm_client import LLMClient
from src.generation.prompt_builder import SYSTEM_PROMPT, build_user_prompt
from src.retrieval.vector_store import VectorStore
from src.schemas import GenerationResult, RetrievedExample


class ReplyGenerator:
    def __init__(self, store: VectorStore, llm: Optional[LLMClient] = None):
        self.store = store
        self.llm = llm or LLMClient()

    def generate(
        self,
        incoming_email: str,
        top_k: int | None = None,
        exclude_id: str | None = None,
    ) -> GenerationResult:
        top_k = top_k or settings.top_k
        retrieved: List[RetrievedExample] = self.store.search(
            incoming_email, top_k=top_k, exclude_id=exclude_id
        )

        user_prompt = build_user_prompt(incoming_email, retrieved)
        # The mock backend grounds itself in the retrieved replies (nearest neighbor).
        mock_context = [r.gold_reply for r in retrieved]
        reply = self.llm.complete(SYSTEM_PROMPT, user_prompt, mock_context=mock_context)

        return GenerationResult(
            incoming_email=incoming_email,
            generated_reply=reply,
            retrieved_examples=retrieved,
            model=self.llm.model,
            used_mock=self.llm.used_mock,
        )
