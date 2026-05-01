from __future__ import annotations

from abc import ABC, abstractmethod
from urllib.parse import urlencode

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.models import DatasetDefinition, HttpRequest


class IngestSource(ABC):
    name: str
    description: str
    documentation_url: str

    @abstractmethod
    def datasets(self) -> tuple[DatasetDefinition, ...]:
        raise NotImplementedError

    @abstractmethod
    def build_request(
        self,
        dataset_name: str,
        params: dict[str, str],
        *,
        config: RuntimeConfig,
        require_credentials: bool,
    ) -> HttpRequest:
        raise NotImplementedError

    def describe(self) -> dict[str, object]:
        return {
            "name": self.name,
            "description": self.description,
            "documentation_url": self.documentation_url,
            "datasets": [dataset.__dict__ for dataset in self.datasets()],
        }

    def _dataset(self, dataset_name: str) -> DatasetDefinition:
        for dataset in self.datasets():
            if dataset.name == dataset_name:
                return dataset
        raise ValueError(f"Unknown dataset `{dataset_name}` for source `{self.name}`")

    def _validate_required(self, dataset: DatasetDefinition, params: dict[str, str]) -> None:
        missing = [name for name in dataset.required_params if not params.get(name)]
        if missing:
            raise ValueError(
                f"Missing required params for `{self.name}:{dataset.name}`: {', '.join(sorted(missing))}"
            )

    def _build_url(self, base_url: str, query: dict[str, str]) -> str:
        return f"{base_url}?{urlencode(query)}" if query else base_url
