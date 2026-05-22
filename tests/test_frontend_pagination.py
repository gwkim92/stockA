from __future__ import annotations

import unittest

from stockanalysis.frontend.pagination import (
    DEFAULT_PAGE_LIMIT,
    FrontendPaginationError,
    apply_frontend_pagination,
    apply_frontend_sql_pagination,
    canonical_frontend_path_for_pagination,
    decode_frontend_cursor,
    encode_frontend_cursor,
    frontend_sql_page_window,
)


def _event_payload(count: int = 3) -> dict[str, object]:
    return {
        "contract_version": "frontend-api-v0.1",
        "generated_at": "2026-05-01T00:00:00Z",
        "data": {
            "as_of_date": "2024-11-01",
            "events": [{"event_id": f"event-{index}"} for index in range(count)],
        },
        "links": {},
    }


def _news_cluster_payload(count: int = 3) -> dict[str, object]:
    return {
        "contract_version": "frontend-api-v0.1",
        "generated_at": "2026-05-01T00:00:00Z",
        "data": {
            "as_of_date": "2026-05-01",
            "clusters": [{"evidence_id": f"ai-evidence-{index}"} for index in range(count)],
        },
        "links": {},
    }


class FrontendPaginationTests(unittest.TestCase):
    def test_limit_slices_collection_and_returns_next_cursor(self) -> None:
        payload = apply_frontend_pagination("/api/events?asOfDate=2024-11-01&limit=2", _event_payload())

        self.assertEqual([item["event_id"] for item in payload["data"]["events"]], ["event-0", "event-1"])
        self.assertEqual(payload["pagination"]["limit"], 2)
        self.assertEqual(payload["pagination"]["item_count"], 2)
        self.assertTrue(payload["pagination"]["has_more"])
        self.assertEqual(decode_frontend_cursor(payload["pagination"]["next_cursor"]), 2)

    def test_cursor_resumes_collection(self) -> None:
        cursor = encode_frontend_cursor(2)
        payload = apply_frontend_pagination(f"/api/events?asOfDate=2024-11-01&limit=2&cursor={cursor}", _event_payload())

        self.assertEqual([item["event_id"] for item in payload["data"]["events"]], ["event-2"])
        self.assertEqual(payload["pagination"]["cursor"], cursor)
        self.assertFalse(payload["pagination"]["has_more"])
        self.assertIsNone(payload["pagination"]["next_cursor"])

    def test_sql_pagination_trims_limit_plus_one_page(self) -> None:
        payload = apply_frontend_sql_pagination("/api/events?asOfDate=2024-11-01&limit=2", _event_payload())

        self.assertEqual([item["event_id"] for item in payload["data"]["events"]], ["event-0", "event-1"])
        self.assertEqual(payload["pagination"]["limit"], 2)
        self.assertEqual(payload["pagination"]["item_count"], 2)
        self.assertTrue(payload["pagination"]["has_more"])
        self.assertEqual(decode_frontend_cursor(payload["pagination"]["next_cursor"]), 2)

    def test_ai_news_cluster_sql_pagination_allows_limit_without_as_of_date(self) -> None:
        payload = apply_frontend_sql_pagination("/api/ai/news-clusters?limit=2", _news_cluster_payload())

        self.assertEqual([item["evidence_id"] for item in payload["data"]["clusters"]], ["ai-evidence-0", "ai-evidence-1"])
        self.assertEqual(payload["pagination"]["limit"], 2)
        self.assertTrue(payload["pagination"]["has_more"])

    def test_sql_page_window_uses_limit_plus_one_and_cursor_offset(self) -> None:
        cursor = encode_frontend_cursor(7)

        page_limit, page_offset = frontend_sql_page_window(
            f"/api/events?asOfDate=2024-11-01&limit=25&cursor={cursor}"
        )

        self.assertEqual(page_limit, 26)
        self.assertEqual(page_offset, 7)

    def test_missing_limit_uses_default(self) -> None:
        payload = apply_frontend_pagination("/api/events?asOfDate=2024-11-01", _event_payload())

        self.assertEqual(payload["pagination"]["limit"], DEFAULT_PAGE_LIMIT)
        self.assertEqual(payload["pagination"]["item_count"], 3)

    def test_invalid_limit_is_rejected(self) -> None:
        with self.assertRaisesRegex(FrontendPaginationError, "between 1 and 100"):
            apply_frontend_pagination("/api/events?asOfDate=2024-11-01&limit=101", _event_payload())

    def test_invalid_cursor_is_rejected(self) -> None:
        with self.assertRaisesRegex(FrontendPaginationError, "cursor is invalid"):
            apply_frontend_pagination("/api/events?asOfDate=2024-11-01&cursor=not-a-cursor", _event_payload())

    def test_pagination_on_non_list_path_is_rejected(self) -> None:
        with self.assertRaisesRegex(FrontendPaginationError, "list endpoints"):
            apply_frontend_pagination(
                "/api/dashboard/today?limit=1",
                {
                    "contract_version": "frontend-api-v0.1",
                    "generated_at": "2026-05-01T00:00:00Z",
                    "data": {},
                    "links": {},
                },
            )

    def test_canonical_path_removes_pagination_params(self) -> None:
        canonical = canonical_frontend_path_for_pagination(
            "/api/remediation-tickets?status=open&limit=1&cursor=abc"
        )

        self.assertEqual(canonical, "/api/remediation-tickets?status=open")


if __name__ == "__main__":
    unittest.main()
