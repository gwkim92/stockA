from __future__ import annotations

import json
import unittest

from stockanalysis.operations.server_scheduler_deployment_decision import (
    build_server_scheduler_deployment_target_decision,
    render_server_scheduler_deployment_target_decision_markdown,
)


class ServerSchedulerDeploymentDecisionTests(unittest.TestCase):
    def test_current_zero_budget_local_only_state_blocks_external_deployment(self) -> None:
        report = build_server_scheduler_deployment_target_decision(
            repo_visibility="public",
            zero_budget_required=True,
            hosted_database_configured=False,
            runtime_host_available=False,
            mac_host_scheduler_allowed=False,
        )

        self.assertEqual(report["report_name"], "server_scheduler_deployment_target_decision")
        self.assertEqual(report["decision_status"], "blocked_missing_hosted_database_or_runtime")
        self.assertEqual(
            report["recommended_target"],
            "github_actions_scheduled_workflow_after_hosted_runtime",
        )
        self.assertIn("external_scheduler_cannot_reach_current_local_postgres", report["blocking_reasons"])
        self.assertFalse(report["scheduler_deployed"])
        self.assertFalse(report["scheduler_deployment_allowed_in_this_task"])
        self.assertFalse(report["host_mutation_allowed"])
        self.assertFalse(report["workflow_file_created"])
        github = _candidate(report, "github_actions_scheduled_workflow")
        self.assertFalse(github["current_ready"])
        self.assertFalse(github["can_reach_current_local_db"])
        self.assertNotIn("postgresql://", json.dumps(report))

    def test_hosted_database_makes_github_actions_recommended_for_public_repo(self) -> None:
        report = build_server_scheduler_deployment_target_decision(
            repo_visibility="public",
            zero_budget_required=True,
            hosted_database_configured=True,
            runtime_host_available=False,
        )

        self.assertEqual(report["decision_status"], "ready_for_scheduler_manifest_task")
        self.assertEqual(report["recommended_target"], "github_actions_scheduled_workflow")
        self.assertEqual(report["blocking_reasons"], [])
        github = _candidate(report, "github_actions_scheduled_workflow")
        self.assertTrue(github["zero_budget_fit"])
        self.assertTrue(github["current_ready"])

    def test_existing_runtime_host_prefers_systemd_timer(self) -> None:
        report = build_server_scheduler_deployment_target_decision(
            repo_visibility="public",
            zero_budget_required=True,
            hosted_database_configured=True,
            runtime_host_available=True,
        )

        self.assertEqual(report["decision_status"], "ready_for_scheduler_manifest_task")
        self.assertEqual(report["recommended_target"], "vps_systemd_timer")
        systemd = _candidate(report, "vps_systemd_timer")
        self.assertTrue(systemd["current_ready"])

    def test_mac_scheduler_is_only_local_option_when_explicitly_allowed(self) -> None:
        report = build_server_scheduler_deployment_target_decision(
            repo_visibility="public",
            zero_budget_required=True,
            hosted_database_configured=False,
            runtime_host_available=False,
            mac_host_scheduler_allowed=True,
        )

        self.assertEqual(report["decision_status"], "ready_for_local_only_scheduler_manifest_task")
        self.assertEqual(report["recommended_target"], "local_host_scheduler")
        local = _candidate(report, "local_host_scheduler")
        self.assertTrue(local["can_reach_current_local_db"])

    def test_invalid_repo_visibility_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            build_server_scheduler_deployment_target_decision(repo_visibility="internal")

    def test_markdown_renderer_is_secret_free_and_mentions_boundary(self) -> None:
        report = build_server_scheduler_deployment_target_decision()

        markdown = render_server_scheduler_deployment_target_decision_markdown(report)

        self.assertIn("Server Scheduler Deployment Target Decision", markdown)
        self.assertIn("blocked_missing_hosted_database_or_runtime", markdown)
        self.assertIn("does not deploy a scheduler", markdown)
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
