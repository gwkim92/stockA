from __future__ import annotations

import json
import unittest

from stockanalysis.operations.hosted_runtime_decision import (
    build_hosted_database_runtime_decision,
    render_hosted_database_runtime_decision_markdown,
)


class HostedRuntimeDecisionTests(unittest.TestCase):
    def test_default_recommends_supabase_setup_before_external_scheduler(self) -> None:
        report = build_hosted_database_runtime_decision()

        self.assertEqual(report["report_name"], "hosted_database_runtime_decision")
        self.assertEqual(report["decision_status"], "setup_required_for_hosted_database")
        self.assertEqual(report["recommended_path"], "supabase_free_postgres_plus_github_actions_worker")
        self.assertIn("hosted_database_not_configured", report["blocking_reasons"])
        self.assertFalse(report["provisioning_performed"])
        self.assertFalse(report["database_created"])
        self.assertFalse(report["secret_written"])
        self.assertFalse(report["workflow_file_created"])
        supabase = _candidate(report, "supabase_free_postgres_plus_github_actions_worker")
        self.assertEqual(supabase["status"], "setup_required")
        self.assertTrue(supabase["zero_budget_fit"])
        self.assertFalse(supabase["external_scheduler_ready"])
        self.assertNotIn("postgresql://", json.dumps(report))

    def test_hosted_database_configured_is_ready_for_migration_smoke(self) -> None:
        report = build_hosted_database_runtime_decision(hosted_database_configured=True)

        self.assertEqual(report["decision_status"], "ready_for_hosted_database_migration_smoke")
        self.assertEqual(report["recommended_path"], "supabase_free_postgres_plus_github_actions_worker")
        self.assertEqual(report["blocking_reasons"], [])
        supabase = _candidate(report, "supabase_free_postgres_plus_github_actions_worker")
        self.assertEqual(supabase["status"], "ready_for_migration_smoke")
        self.assertTrue(supabase["external_scheduler_ready"])

    def test_existing_runtime_host_is_preferred_when_available(self) -> None:
        report = build_hosted_database_runtime_decision(
            hosted_database_configured=True,
            existing_runtime_host_available=True,
        )

        self.assertEqual(report["decision_status"], "ready_for_existing_host_runtime_smoke")
        self.assertEqual(report["recommended_path"], "existing_host_postgres_plus_systemd_worker")
        existing_host = _candidate(report, "existing_host_postgres_plus_systemd_worker")
        self.assertEqual(existing_host["status"], "ready_for_host_runtime_smoke")
        self.assertTrue(existing_host["external_scheduler_ready"])

    def test_local_only_accepted_is_explicitly_not_external_scheduler_ready(self) -> None:
        report = build_hosted_database_runtime_decision(local_only_accepted=True)

        self.assertEqual(report["decision_status"], "local_only_runtime_selected")
        self.assertEqual(report["recommended_path"], "local_only_postgres_plus_local_worker")
        self.assertIn("external_scheduler_not_enabled_by_choice", report["blocking_reasons"])
        local = _candidate(report, "local_only_postgres_plus_local_worker")
        self.assertEqual(local["status"], "local_only_ready")
        self.assertFalse(local["external_scheduler_ready"])

    def test_no_supabase_capacity_blocks_free_hosted_database_path(self) -> None:
        report = build_hosted_database_runtime_decision(supabase_free_project_available=False)

        self.assertEqual(report["decision_status"], "blocked_no_free_hosted_database_capacity")
        self.assertEqual(report["recommended_path"], "blocked_no_free_hosted_database_capacity")
        self.assertIn("no_free_hosted_database_candidate_confirmed", report["blocking_reasons"])

    def test_invalid_repo_visibility_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            build_hosted_database_runtime_decision(repo_visibility="internal")

    def test_markdown_renderer_is_secret_free(self) -> None:
        report = build_hosted_database_runtime_decision()

        markdown = render_hosted_database_runtime_decision_markdown(report)

        self.assertIn("Hosted Database Runtime Decision", markdown)
        self.assertIn("setup_required_for_hosted_database", markdown)
        self.assertIn("does not create a database", markdown)
        self.assertNotIn("postgresql://", markdown)


def _candidate(report: dict[str, object], target: str) -> dict[str, object]:
    candidates = report["candidate_matrix"]
    assert isinstance(candidates, list)
    for candidate in candidates:
        if isinstance(candidate, dict) and candidate.get("target") == target:
            return candidate
    raise AssertionError(f"missing candidate: {target}")


if __name__ == "__main__":
    unittest.main()
