from __future__ import annotations

from urllib.request import Request, urlopen

from .models import FetchResponse, HttpRequest


def execute_request(request: HttpRequest) -> FetchResponse:
    raw_request = Request(
        request.url,
        headers=request.headers,
        method=request.method,
    )
    with urlopen(raw_request, timeout=request.timeout_seconds) as response:
        return FetchResponse(
            status_code=response.status,
            content_type=response.headers.get_content_type(),
            body=response.read(),
        )
