"""Small deterministic checks at evidence boundaries; not semantic verification."""
from __future__ import annotations

from collections.abc import Iterable
from stockanalysis.ai_agents.prompt_contract import PromptContractError, validate_output


def probability(value: object) -> float:
    """Accept an actual finite JSON number in [0, 1]; never coerce or clamp."""
    validate_output(value, {"type": "number", "minimum": 0, "maximum": 1})
    return float(value)


def same_document(source_id: object, chunk_id: object) -> None:
    if type(source_id) is not int or source_id <= 0 or type(chunk_id) is not int or source_id != chunk_id:
        raise PromptContractError("source_chunk_identity_mismatch")


def validate_literal_spans(spans: Iterable[str], *, title: str, summary: str) -> None:
    """Whitespace-tolerant literal matching within either original source field.

    Metadata, retrieved news and translations are not the original. Exact span
    membership does not prove its supporting claim or causal interpretation.
    Empty span collections remain allowed by the existing output schema.
    """
    originals = [" ".join(part.split()) for part in (title, summary) if isinstance(part, str)]
    for span in spans:
        if not isinstance(span, str):
            raise PromptContractError("evidence_span_not_in_source")
        normalized = " ".join(span.split())
        if not normalized or not any(normalized in original for original in originals):
            raise PromptContractError("evidence_span_not_in_source")
