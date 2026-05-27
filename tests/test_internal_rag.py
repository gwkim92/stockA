from datetime import date
import json
import unittest

from stockanalysis.ai.internal_rag import build_internal_rag_context_package


class InternalRagContextTests(unittest.TestCase):
    def test_builds_secret_free_postgres_context_package(self) -> None:
        package = build_internal_rag_context_package(
            symbol="NVDA",
            as_of_date=date(2026, 5, 27),
            instrument={"symbol": "NVDA", "name": "NVIDIA Corporation", "market_code": "US", "found": True},
            themes=[
                {
                    "theme_key": "AI_SEMICONDUCTOR_CYCLE",
                    "theme_name": "AI Semiconductor Cycle",
                    "membership_type": "seeded",
                    "confidence": 0.91,
                    "node_type": "theme",
                    "taxonomy_family": "internal_theme",
                }
            ],
            theme_edges=[
                {
                    "parent_theme_key": "TECH_DOMAIN",
                    "child_theme_key": "AI_SEMICONDUCTOR_CYCLE",
                    "relation_type": "contains",
                    "weight": 0.8,
                }
            ],
            events=[
                {
                    "event_id": "event-1",
                    "title": "NVIDIA reports datacenter demand",
                    "korean_title": "엔비디아 데이터센터 수요 뉴스",
                    "korean_summary": "AI 데이터센터 수요가 실적 기대에 연결된다.",
                    "event_at": "2026-05-27T10:00:00Z",
                    "theme_key": "AI_SEMICONDUCTOR_CYCLE",
                    "impact_direction": "supportive",
                    "impact_score": 0.78,
                    "source_document_id": "source-document-1",
                }
            ],
            story_groups=[
                {
                    "story_id": "story-1",
                    "korean_title": "AI 반도체 수요 묶음",
                    "event_count": 2,
                    "relation_reasons": ["같은 테마", "같은 종목"],
                    "theme_keys": ["AI_SEMICONDUCTOR_CYCLE"],
                    "source_document_ids": ["source-document-1"],
                }
            ],
            ai_artifacts=[
                {
                    "evidence_id": "ai-evidence-1",
                    "evidence_type": "news_event_candidate",
                    "provider": "codex_oauth",
                    "status": "succeeded",
                    "confidence": 0.86,
                    "model_id": "codex-cli-default",
                }
            ],
            evidence_chunks=[
                {
                    "chunk_id": "chunk-1",
                    "source_document_id": "source-document-1",
                    "chunk_index": 0,
                    "text_preview": "Datacenter revenue increased as AI demand grew.",
                    "token_count": 21,
                    "source_url_host": "example.com",
                    "source_text_kind": "raw_html_text",
                    "embedding_status": "indexed",
                    "vector_storage_uri": "secret://must-not-leak",
                }
            ],
            theses=[
                {
                    "thesis_id": "thesis-1",
                    "title": "AI accelerator compounder thesis",
                    "status": "active",
                    "conviction_score": 0.74,
                    "expected_holding_days": 730,
                    "invalidation_conditions": "Datacenter margin reversal.",
                }
            ],
            recommendations=[
                {
                    "recommendation_id": "recommendation-1",
                    "as_of_date": "2026-05-27",
                    "action": "accumulate",
                    "bucket": "long_term_core",
                    "total_score": 0.71,
                    "recommended_weight": 0.05,
                    "linked_thesis_id": "thesis-1",
                }
            ],
            positions=[],
        )

        self.assertEqual(package["status"], "ready")
        self.assertEqual(package["retrieval_policy"]["retrieval_backend"], "postgres_sql_graph_context")
        self.assertFalse(package["retrieval_policy"]["live_llm_call_enabled"])
        self.assertFalse(package["retrieval_policy"]["write_enabled"])
        self.assertEqual(package["context_inventory"]["translated_event_count"], 1)
        self.assertEqual(package["quality_gates"][0]["status"], "passed")
        self.assertIn("엔비디아 데이터센터 수요 뉴스", package["prompt_context"]["context_text"])
        serialized = json.dumps(package, ensure_ascii=False)
        self.assertNotIn("vector_storage_uri", serialized)
        self.assertNotIn("secret://", serialized)

    def test_marks_missing_translation_and_source_grounding_as_attention(self) -> None:
        package = build_internal_rag_context_package(
            symbol="SPY",
            as_of_date="2026-05-27",
            instrument={"symbol": "SPY", "name": "SPDR S&P 500 ETF Trust", "market_code": "US", "found": True},
            themes=[],
            theme_edges=[],
            events=[{"event_id": "event-2", "title": "Fed policy update", "impact_direction": "watch"}],
            story_groups=[],
            ai_artifacts=[],
            evidence_chunks=[],
            theses=[],
            recommendations=[],
            positions=[],
        )

        gate_status = {gate["gate"]: gate["status"] for gate in package["quality_gates"]}
        self.assertEqual(gate_status["korean_translation"], "attention")
        self.assertEqual(gate_status["source_grounding"], "attention")
        self.assertEqual(gate_status["ai_artifact_linkage"], "attention")
        self.assertEqual(gate_status["decision_linkage"], "watch")

    def test_rejects_too_small_context_budget(self) -> None:
        with self.assertRaises(ValueError):
            build_internal_rag_context_package(
                symbol="AAPL",
                as_of_date=date(2026, 5, 27),
                instrument={},
                themes=[],
                theme_edges=[],
                events=[],
                story_groups=[],
                ai_artifacts=[],
                evidence_chunks=[],
                theses=[],
                recommendations=[],
                positions=[],
                context_char_budget=100,
            )


if __name__ == "__main__":
    unittest.main()
