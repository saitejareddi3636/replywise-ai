"""Load and validate the JSONL dataset into typed `EmailExample` objects."""

from __future__ import annotations

from pathlib import Path
from typing import List

from src.config import DATA_DIR
from src.schemas import EmailExample


def load_examples(path: Path | str) -> List[EmailExample]:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Generate it first: python -m src.dataset.generate_dataset"
        )
    examples: List[EmailExample] = []
    with path.open("r", encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                examples.append(EmailExample.model_validate_json(line))
            except Exception as exc:  # surface the offending line for fast debugging
                raise ValueError(f"invalid record on line {line_no} of {path}: {exc}") from exc
    return examples


def load_train() -> List[EmailExample]:
    return load_examples(DATA_DIR / "synthetic_emails.jsonl")


def load_test() -> List[EmailExample]:
    return load_examples(DATA_DIR / "test_emails.jsonl")
