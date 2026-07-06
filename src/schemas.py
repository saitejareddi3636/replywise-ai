"""Pydantic schemas shared across ReplyWise AI.

These types are the single source of truth for the shape of the dataset,
the generation output, and every evaluation artifact. Keeping them in one
place means the dataset script, the RAG pipeline, the API, and the tests all
agree on field names and validation rules.
"""

from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class Category(str, Enum):
    SCHEDULING = "scheduling"
    RECRUITING = "recruiting"
    CUSTOMER_SUPPORT = "customer_support"
    SALES_DEMO = "sales_demo"
    INVOICE_PAYMENT = "invoice_payment"
    PROJECT_UPDATE = "project_update"
    PARTNERSHIP = "partnership"
    EVENT_LOGISTICS = "event_logistics"
    COMPLAINT_ESCALATION = "complaint_escalation"
    FOLLOW_UP = "follow_up"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class EmailExample(BaseModel):
    """A single labeled email/reply pair.

    The `gold_reply` plus the control fields (`required_facts`, `must_include`,
    `must_not_include`, ...) are what make evaluation meaningful: they encode
    what a *correct* reply must and must not do, independent of exact wording.
    """

    id: str
    category: Category
    intent: str
    tone: str
    incoming_email: str
    gold_reply: str
    required_facts: List[str] = Field(default_factory=list)
    must_include: List[str] = Field(default_factory=list)
    must_not_include: List[str] = Field(default_factory=list)
    ideal_action: str = ""
    risk_level: RiskLevel = RiskLevel.LOW

    @field_validator("incoming_email", "gold_reply")
    @classmethod
    def _non_empty(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("email text must not be empty")
        return value.strip()


class RetrievedExample(BaseModel):
    """A neighbor returned by the vector store, with its similarity score."""

    id: str
    category: str
    intent: str
    tone: str
    incoming_email: str
    gold_reply: str
    score: float


class GenerationResult(BaseModel):
    """Output of the RAG pipeline for one incoming email."""

    incoming_email: str
    generated_reply: str
    retrieved_examples: List[RetrievedExample] = Field(default_factory=list)
    model: str
    used_mock: bool = False


class MetricBreakdown(BaseModel):
    """Per-metric scores in [0, 1] before weighting."""

    semantic_similarity: float
    required_fact_coverage: float
    must_include_coverage: float
    must_not_include_violation: float  # 0 = clean, 1 = every forbidden item present
    intent_alignment: float
    tone_match: float
    helpfulness: float
    safety_no_hallucination: float
    judge_score: Optional[float] = None  # LLM-as-judge, may be None if disabled


class EvaluationResult(BaseModel):
    """Everything we know about how one generated reply performed."""

    id: str
    category: str
    incoming_email: str
    gold_reply: str
    generated_reply: str
    retrieved_examples: List[RetrievedExample] = Field(default_factory=list)
    metrics: MetricBreakdown
    final_score: float
    passed: bool
    explanation: str


class CategoryScore(BaseModel):
    category: str
    count: int
    average_score: float
    pass_rate: float


class EvaluationReport(BaseModel):
    """Aggregate report over an evaluation run."""

    num_examples: int
    average_score: float
    pass_rate: float
    pass_threshold: float
    category_scores: List[CategoryScore]
    best_examples: List[EvaluationResult]
    worst_examples: List[EvaluationResult]
    common_failure_types: dict
    results: List[EvaluationResult]
