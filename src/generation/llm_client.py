"""LLM client with three backends: Anthropic, OpenAI-compatible, and a mock.

The mock backend is a first-class citizen, not an afterthought: if no API key is
configured the pipeline still produces a *retrieval-grounded* reply by adapting
the closest past reply. That keeps the demo, the API, and the full evaluation
runnable with zero credentials, and gives us a meaningful nearest-neighbor
baseline to compare a real model against.
"""

from __future__ import annotations

from typing import List, Optional

from src.config import settings


class LLMClient:
    def __init__(self):
        self.provider = settings.provider  # "groq" | "anthropic" | "openai" | "mock"
        self.model = settings.resolved_model if self.provider != "mock" else "mock-nn-baseline"
        self._client = None
        if self.provider == "anthropic":
            self._init_anthropic()
        elif self.provider == "openai":
            self._init_openai()
        elif self.provider == "groq":
            self._init_groq()

    def _fallback_to_mock(self) -> None:
        self.provider = "mock"
        self.model = "mock-nn-baseline"

    def _init_anthropic(self) -> None:
        try:
            import anthropic

            self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        except Exception:
            self._fallback_to_mock()

    def _init_openai(self) -> None:
        try:
            from openai import OpenAI

            self._client = OpenAI(api_key=settings.openai_api_key)
        except Exception:
            self._fallback_to_mock()

    def _init_groq(self) -> None:
        # Groq is OpenAI-compatible: reuse the OpenAI SDK with Groq's base URL.
        try:
            from openai import OpenAI

            self._client = OpenAI(api_key=settings.groq_api_key, base_url=settings.groq_base_url)
        except Exception:
            self._fallback_to_mock()

    @property
    def used_mock(self) -> bool:
        return self.provider == "mock"

    def complete(self, system: str, user: str, mock_context: Optional[List[str]] = None) -> str:
        if self.provider == "anthropic":
            return self._complete_anthropic(system, user)
        if self.provider in ("openai", "groq"):  # both use the chat.completions API
            return self._complete_openai(system, user)
        return self._complete_mock(mock_context)

    def _complete_anthropic(self, system: str, user: str) -> str:
        resp = self._client.messages.create(
            model=self.model,
            max_tokens=settings.max_tokens,
            temperature=settings.temperature,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(block.text for block in resp.content if getattr(block, "type", "") == "text").strip()

    def _complete_openai(self, system: str, user: str) -> str:
        resp = self._client.chat.completions.create(
            model=self.model,
            max_tokens=settings.max_tokens,
            temperature=settings.temperature,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return (resp.choices[0].message.content or "").strip()

    def _complete_mock(self, mock_context: Optional[List[str]]) -> str:
        """Deterministic nearest-neighbor reply.

        We return the single most similar past reply (the top retrieved gold
        reply), which is a fair, reproducible baseline. It exercises every
        downstream metric without any API access.
        """
        if mock_context:
            return mock_context[0].strip()
        return (
            "Thanks for your message. I want to make sure I give you an accurate answer, "
            "so could you share a bit more detail? I'll follow up promptly."
        )
