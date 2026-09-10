"""Select complete context records without weakening the source-data size guard."""
from __future__ import annotations

from copy import deepcopy

from stockanalysis.ai_agents.prompt_contract import PromptContractError, render_source_data


def select_source_records(
    payload: dict[str, object],
    *,
    record_paths: tuple[tuple[str, ...], ...],
    max_chars: int,
) -> dict[str, object]:
    """Keep required fields intact, then fit records in deterministic round-robin order.

    Validate all input before selection. Oversized metadata still fails closed;
    only the caller's explicit record collections can be reduced. Every omitted
    record is counted in the framed source and therefore in its fingerprint.
    """
    try:
        render_source_data(payload, max_chars=max_chars)
        return deepcopy(payload)
    except PromptContractError as exc:
        if str(exc) != "input_budget_exceeded":
            raise

    result = deepcopy(payload)
    collections = []
    for path in record_paths:
        container = result
        for key in path[:-1]:
            container = container[key]
        rows = container[path[-1]]
        if not isinstance(rows, list):
            raise PromptContractError("invalid_record_collection")
        container[path[-1]] = []
        collections.append((".".join(path), container[path[-1]], rows))
    selection = {
        "mode": "complete_records_with_explicit_omissions_v1",
        "available": {key: len(rows) for key, _, rows in collections},
        "omitted": {key: len(rows) for key, _, rows in collections},
    }
    result["input_selection"] = selection
    render_source_data(result, max_chars=max_chars)

    for index in range(max((len(rows) for _, _, rows in collections), default=0)):
        for key, selected, rows in collections:
            if index >= len(rows):
                continue
            selected.append(rows[index])
            selection["omitted"][key] -= 1
            try:
                render_source_data(result, max_chars=max_chars)
            except PromptContractError as exc:
                if str(exc) != "input_budget_exceeded":
                    raise
                selected.pop()
                selection["omitted"][key] += 1
    return result
