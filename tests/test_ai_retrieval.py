import unittest

from stockanalysis.ai.retrieval import InMemoryRetrievalAdapter, RetrievalQuery, RetrievalResult


class AiRetrievalTests(unittest.TestCase):
    def test_in_memory_retrieval_adapter_returns_matching_chunks_by_score(self) -> None:
        adapter = InMemoryRetrievalAdapter(
            [
                RetrievalResult(
                    chunk_id=1,
                    document_id=10,
                    score=0.72,
                    text_preview="annual report revenue growth",
                    source_uri="adapter://test/document/10/chunk/0",
                ),
                RetrievalResult(
                    chunk_id=2,
                    document_id=11,
                    score=0.91,
                    text_preview="risk factors include export controls and China restrictions",
                    source_uri="adapter://test/document/11/chunk/0",
                ),
                RetrievalResult(
                    chunk_id=3,
                    document_id=12,
                    score=0.64,
                    text_preview="capital return and dividend policy",
                    source_uri="adapter://test/document/12/chunk/0",
                ),
            ]
        )

        results = adapter.search(RetrievalQuery(text="risk China", limit=5))

        self.assertEqual([item.chunk_id for item in results], [2])

    def test_in_memory_retrieval_adapter_enforces_limit(self) -> None:
        adapter = InMemoryRetrievalAdapter(
            [
                RetrievalResult(1, 10, 0.4, "AI accelerator demand", "adapter://chunk/1"),
                RetrievalResult(2, 11, 0.9, "AI memory demand", "adapter://chunk/2"),
                RetrievalResult(3, 12, 0.7, "AI datacenter demand", "adapter://chunk/3"),
            ]
        )

        results = adapter.search(RetrievalQuery(text="AI demand", limit=2))

        self.assertEqual([item.chunk_id for item in results], [2, 3])

    def test_retrieval_query_rejects_empty_text_and_invalid_limit(self) -> None:
        with self.assertRaises(ValueError):
            RetrievalQuery(text="   ")
        with self.assertRaises(ValueError):
            RetrievalQuery(text="risk", limit=0)


if __name__ == "__main__":
    unittest.main()
