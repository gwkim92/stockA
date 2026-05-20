from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class RetrievalQuery:
    text: str
    limit: int = 10
    filters: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        text = self.text.strip()
        if not text:
            raise ValueError("Retrieval query text must not be empty.")
        if self.limit < 1 or self.limit > 100:
            raise ValueError("Retrieval query limit must be between 1 and 100.")
        object.__setattr__(self, "text", text)


@dataclass(frozen=True)
class RetrievalResult:
    chunk_id: int
    document_id: int
    score: float
    text_preview: str
    source_uri: str
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.chunk_id < 1:
            raise ValueError("Retrieval result chunk_id must be positive.")
        if self.document_id < 1:
            raise ValueError("Retrieval result document_id must be positive.")
        if not 0 <= self.score <= 1:
            raise ValueError("Retrieval result score must be between 0 and 1.")
        if not self.source_uri.strip():
            raise ValueError("Retrieval result source_uri must not be empty.")


class RetrievalAdapter(Protocol):
    def search(self, query: RetrievalQuery) -> list[RetrievalResult]:
        """Return ranked evidence chunks for a query."""


class InMemoryRetrievalAdapter:
    """Deterministic adapter used by tests before a real vector backend exists."""

    def __init__(self, results: Iterable[RetrievalResult]) -> None:
        self._results = tuple(results)

    def search(self, query: RetrievalQuery) -> list[RetrievalResult]:
        terms = _query_terms(query.text)
        matched = [result for result in self._results if _matches(result, terms, query.filters)]
        return sorted(matched, key=lambda result: (-result.score, result.chunk_id))[: query.limit]


def _query_terms(text: str) -> tuple[str, ...]:
    return tuple(term.casefold() for term in text.split() if term.strip())


def _matches(result: RetrievalResult, terms: tuple[str, ...], filters: Mapping[str, str]) -> bool:
    for key, value in filters.items():
        if result.metadata.get(key) != value:
            return False

    haystack = " ".join(
        [
            result.text_preview,
            result.source_uri,
            " ".join(result.metadata.values()),
        ]
    ).casefold()
    return all(term in haystack for term in terms)
