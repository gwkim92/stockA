"""Small deterministic checks at evidence boundaries; not semantic verification."""
from __future__ import annotations

from stockanalysis.ai_agents.prompt_contract import PromptContractError, validate_output


def probability(value: object) -> float:
    """Accept an actual finite JSON number in [0, 1]; never coerce or clamp."""
    validate_output(value, {"type": "number", "minimum": 0, "maximum": 1})
    return float(value)


def same_document(source_id: object, chunk_id: object) -> None:
    if type(source_id) is not int or source_id <= 0 or type(chunk_id) is not int or source_id != chunk_id:
        raise PromptContractError("source_chunk_identity_mismatch")

