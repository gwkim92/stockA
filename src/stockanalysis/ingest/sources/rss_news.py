from __future__ import annotations

from urllib.parse import urlparse

from stockanalysis.ingest.config import RuntimeConfig
from stockanalysis.ingest.models import DatasetDefinition, HttpRequest
from stockanalysis.ingest.sources.base import IngestSource


class RssNewsSource(IngestSource):
    name = "rss_news"
    description = "Credential-free RSS/Atom news feed source."
    documentation_url = "https://www.rssboard.org/rss-specification"

    def datasets(self) -> tuple[DatasetDefinition, ...]:
        return (
            DatasetDefinition(
                name="feed",
                description="Fetch a public RSS or Atom feed URL without API credentials.",
                documentation_url=self.documentation_url,
                required_params=("url",),
                optional_params=("timeout_seconds", "user_agent"),
                notes=(
                    "The source adapter only builds a read request; publisher license and usage rules remain operator-owned.",
                    "Use fixture XML for deterministic local smoke tests.",
                ),
            ),
        )

    def build_request(
        self,
        dataset_name: str,
        params: dict[str, str],
        *,
        config: RuntimeConfig,
        require_credentials: bool,
    ) -> HttpRequest:
        del config, require_credentials
        dataset = self._dataset(dataset_name)
        self._validate_required(dataset, params)
        url = params["url"].strip()
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("rss_news feed url must be an absolute http(s) URL")
        timeout_seconds = float(params.get("timeout_seconds") or 30.0)
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be greater than 0")
        return HttpRequest(
            source_name=self.name,
            dataset_name=dataset.name,
            method="GET",
            url=url,
            headers={
                "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml;q=0.9, */*;q=0.5",
                "User-Agent": params.get("user_agent") or "stockanalysis-rss-ingest/0.1",
            },
            timeout_seconds=timeout_seconds,
        )
