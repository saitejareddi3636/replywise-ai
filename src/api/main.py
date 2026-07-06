"""FastAPI service exposing the RAG reply pipeline and the evaluator.

Endpoints:
    GET  /health                 -> service + backend status
    POST /suggest                -> generate a suggested reply for an email
    POST /evaluate               -> generate a reply and score it against labels

The vector store is built once at startup from the persisted index (falling back
to building from the dataset on the fly if no index exists yet).
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from src.config import INDEX_DIR, settings
from src.dataset.load_dataset import load_train
from src.evaluation.evaluator import Evaluator
from src.generation.reply_generator import ReplyGenerator
from src.retrieval.embedder import Embedder
from src.retrieval.vector_store import VectorStore
from src.schemas import EmailExample, EvaluationResult, GenerationResult, RiskLevel

_state: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    embedder = Embedder()
    store = VectorStore(embedder)
    try:
        store.load(INDEX_DIR)
    except Exception:
        store.build(load_train())
    _state["store"] = store
    _state["generator"] = ReplyGenerator(store)
    _state["evaluator"] = Evaluator(embedder=embedder)
    yield
    _state.clear()


app = FastAPI(
    title="ReplyWise AI",
    version="1.0.0",
    description="Retrieval-grounded email reply assistant",
    lifespan=lifespan,
)


class SuggestRequest(BaseModel):
    incoming_email: str = Field(..., min_length=1)
    top_k: Optional[int] = None


class EvaluateRequest(BaseModel):
    incoming_email: str = Field(..., min_length=1)
    gold_reply: str = Field(..., min_length=1)
    category: str = "follow_up"
    intent: str = "respond"
    tone: str = "professional"
    required_facts: List[str] = Field(default_factory=list)
    must_include: List[str] = Field(default_factory=list)
    must_not_include: List[str] = Field(default_factory=list)
    ideal_action: str = ""
    top_k: Optional[int] = None


@app.get("/health")
def health() -> dict:
    gen = _state.get("generator")
    provider = gen.llm.provider if gen else settings.provider
    return {
        "status": "ok",
        "llm_provider": provider,
        "llm_model": gen.llm.model if gen else settings.llm_model,
        "embedding_backend": _state["store"].embedder.backend if "store" in _state else "unknown",
        "indexed_examples": len(_state["store"].examples) if "store" in _state else 0,
        "using_mock_llm": provider == "mock",
    }


@app.post("/suggest", response_model=GenerationResult)
def suggest(req: SuggestRequest) -> GenerationResult:
    if "generator" not in _state:
        raise HTTPException(503, "service not ready")
    return _state["generator"].generate(req.incoming_email, top_k=req.top_k)


@app.post("/evaluate", response_model=EvaluationResult)
def evaluate(req: EvaluateRequest) -> EvaluationResult:
    if "generator" not in _state:
        raise HTTPException(503, "service not ready")
    gen = _state["generator"].generate(req.incoming_email, top_k=req.top_k)
    example = EmailExample(
        id="adhoc",
        category=req.category,
        intent=req.intent,
        tone=req.tone,
        incoming_email=req.incoming_email,
        gold_reply=req.gold_reply,
        required_facts=req.required_facts,
        must_include=req.must_include,
        must_not_include=req.must_not_include,
        ideal_action=req.ideal_action,
        risk_level=RiskLevel.LOW,
    )
    return _state["evaluator"].evaluate_generation(example, gen)
