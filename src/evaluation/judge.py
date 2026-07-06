"""Optional LLM-as-judge.

This is a *complement* to the deterministic metrics, not a replacement. It asks
a model to grade the reply on the same axes and return strict JSON. It is off by
default (`REPLYWISE_USE_JUDGE=true` to enable) and degrades gracefully to `None`
when no API key is available, so the core evaluation never depends on it.
"""

from __future__ import annotations

import json
import re
from typing import Optional

from pydantic import BaseModel, Field

from src.config import settings
from src.generation.llm_client import LLMClient
from src.schemas import EmailExample

JUDGE_SYSTEM = """You are a strict but fair evaluator of customer/business email replies.
Score the CANDIDATE reply against the incoming email and a reference (gold) reply.
Return ONLY valid JSON, no prose, with this exact shape:
{
  "correctness": 0.0-1.0,
  "tone": 0.0-1.0,
  "helpfulness": 0.0-1.0,
  "safety": 0.0-1.0,
  "overall": 0.0-1.0,
  "reasoning": "one or two sentences"
}
Judge substance and usefulness, not surface wording. Penalize invented facts heavily under "safety"."""


class JudgeVerdict(BaseModel):
    correctness: float = Field(ge=0.0, le=1.0)
    tone: float = Field(ge=0.0, le=1.0)
    helpfulness: float = Field(ge=0.0, le=1.0)
    safety: float = Field(ge=0.0, le=1.0)
    overall: float = Field(ge=0.0, le=1.0)
    reasoning: str = ""


class Judge:
    def __init__(self, llm: Optional[LLMClient] = None):
        self.llm = llm or LLMClient()
        self.enabled = settings.use_judge and not self.llm.used_mock

    def score(self, example: EmailExample, generated_reply: str) -> Optional[JudgeVerdict]:
        if not self.enabled:
            return None
        user = (
            f"INCOMING EMAIL:\n{example.incoming_email}\n\n"
            f"GOLD REFERENCE REPLY:\n{example.gold_reply}\n\n"
            f"CANDIDATE REPLY:\n{generated_reply}\n\n"
            "Return the JSON verdict now."
        )
        try:
            raw = self.llm.complete(JUDGE_SYSTEM, user)
            return JudgeVerdict.model_validate(_extract_json(raw))
        except Exception:
            return None


def _extract_json(raw: str) -> dict:
    match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
    if not match:
        raise ValueError("no JSON object found in judge output")
    return json.loads(match.group(0))
