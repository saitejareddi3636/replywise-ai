"""Central configuration, resolved from environment variables.

Every knob has a sensible default so the project runs end-to-end with zero
setup. If no LLM API key is present the pipeline transparently falls back to a
deterministic mock generator, which keeps the demo and the test suite runnable
offline.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

try:  # optional: load a local .env if python-dotenv is installed
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # pragma: no cover - dotenv is a convenience, not a requirement
    pass


ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
OUTPUT_DIR = ROOT / "outputs"
INDEX_DIR = ROOT / "outputs" / "index"


def _weights() -> dict:
    """Final-score weights. Sum to 1.0; validated at import time."""
    return {
        "semantic_similarity": 0.20,
        "required_fact_coverage": 0.25,
        "intent_alignment": 0.15,
        "tone_match": 0.10,
        "helpfulness": 0.15,
        "safety_no_hallucination": 0.15,
    }


@dataclass
class Settings:
    # --- Generation ---
    anthropic_api_key: str = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    groq_api_key: str = field(default_factory=lambda: os.getenv("GROQ_API_KEY", ""))
    groq_base_url: str = field(
        default_factory=lambda: os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
    )
    # Optional hard override: "groq" | "anthropic" | "openai" | "mock".
    provider_override: str = field(default_factory=lambda: os.getenv("REPLYWISE_PROVIDER", "").lower())
    llm_model: str = field(default_factory=lambda: os.getenv("REPLYWISE_MODEL", ""))
    max_tokens: int = field(default_factory=lambda: int(os.getenv("REPLYWISE_MAX_TOKENS", "600")))
    temperature: float = field(default_factory=lambda: float(os.getenv("REPLYWISE_TEMPERATURE", "0.3")))

    # --- Retrieval ---
    embedding_model: str = field(
        default_factory=lambda: os.getenv("REPLYWISE_EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    )
    top_k: int = field(default_factory=lambda: int(os.getenv("REPLYWISE_TOP_K", "4")))

    # --- Evaluation ---
    pass_threshold: float = field(default_factory=lambda: float(os.getenv("REPLYWISE_PASS_THRESHOLD", "0.70")))
    use_judge: bool = field(default_factory=lambda: os.getenv("REPLYWISE_USE_JUDGE", "false").lower() == "true")
    must_not_include_penalty: float = field(
        default_factory=lambda: float(os.getenv("REPLYWISE_MNI_PENALTY", "0.5"))
    )

    weights: dict = field(default_factory=_weights)

    # Sensible default model per provider, used when REPLYWISE_MODEL is unset.
    _DEFAULT_MODELS = {
        "anthropic": "claude-sonnet-5",
        "openai": "gpt-4o-mini",
        "groq": "llama-3.3-70b-versatile",
    }

    @property
    def has_llm(self) -> bool:
        return bool(self.anthropic_api_key or self.openai_api_key or self.groq_api_key)

    @property
    def provider(self) -> str:
        if self.provider_override in {"groq", "anthropic", "openai", "mock"}:
            # Honor an explicit override only if its key is present (or it's mock).
            key = {
                "groq": self.groq_api_key,
                "anthropic": self.anthropic_api_key,
                "openai": self.openai_api_key,
                "mock": "x",
            }[self.provider_override]
            if key:
                return self.provider_override
        if self.groq_api_key:
            return "groq"
        if self.anthropic_api_key:
            return "anthropic"
        if self.openai_api_key:
            return "openai"
        return "mock"

    @property
    def resolved_model(self) -> str:
        if self.llm_model:
            return self.llm_model
        return self._DEFAULT_MODELS.get(self.provider, "mock-nn-baseline")

    def validate(self) -> None:
        total = sum(self.weights.values())
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"final-score weights must sum to 1.0, got {total:.4f}")


settings = Settings()
settings.validate()


def weighted_metrics() -> List[str]:
    return list(settings.weights.keys())
