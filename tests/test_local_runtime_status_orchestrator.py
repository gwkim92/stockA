from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from stockanalysis.operations.local_runtime_status import build_local_first_runtime_status_report


class LocalRuntimeStatusOrchestratorTests(unittest.TestCase):
    def test_ready_report_redacts_env_values_and_blocks_host_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as runtime_root:
            runtime_path = Path(runtime_root)
            artifact_root = runtime_path / "artifacts"
            artifact_root.mkdir()
            frontend_env = runtime_path / "frontend-api.env"
            data_env = runtime_path / "data-operations.env"
            frontend_env.write_text(
                "\n".join(
                    [
                        'STOCKANALYSIS_DATABASE_URL="postgresql://user:very-hidden-db-password@localhost/db"',
                        'STOCKANALYSIS_FRONTEND_API_READ_TOKEN="very-hidden-read-token"',
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            data_env.write_text(
                "\n".join(
                    [
                        f'STOCKANALYSIS_DATA_OPERATIONS_ARTIFACT_ROOT="{artifact_root}"',
                        'STOCKANALYSIS_TWELVE_DATA_API_KEY="very-hidden-twelve-key"',
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            report = build_local_first_runtime_status_report(
                repo_root=repo_root,
                runtime_root=runtime_path,
                url_probe=_ok_probe,
            )

            self.assertEqual(report["report_name"], "local_first_runtime_status")
            self.assertEqual(report["overall_status"], "ready")
            self.assertFalse(report["codex_host_mutation_allowed"])
            self.assertFalse(report["launchagents_install_allowed"])
            self.assertGreaterEqual(len(report["why_launchagents_blocked"]), 3)
            report_text = json.dumps(report)
            self.assertNotIn("very-hidden-db-password", report_text)
            self.assertNotIn("very-hidden-read-token", report_text)
            self.assertNotIn("very-hidden-twelve-key", report_text)
            self.assertIn("STOCKANALYSIS_DATABASE_URL", report_text)

    def test_missing_local_runtime_parts_are_actionable(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as outside_root:
            missing_runtime = Path(outside_root) / "missing-runtime"

            report = build_local_first_runtime_status_report(
                repo_root=repo_root,
                runtime_root=missing_runtime,
                skip_http_probes=True,
            )

            self.assertEqual(report["overall_status"], "needs_attention")
            self.assertIn("prepare repo-outside frontend-api.env", report["next_actions"])
            self.assertIn("prepare repo-outside data-operations.env", report["next_actions"])
            self.assertIn("configure STOCKANALYSIS_DATABASE_URL or STOCKANALYSIS_PSQL_COMMAND", report["next_actions"])

    def test_unreachable_endpoint_is_reported_without_starting_services(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as runtime_root:
            runtime_path = Path(runtime_root)
            artifact_root = runtime_path / "artifacts"
            artifact_root.mkdir()
            (runtime_path / "frontend-api.env").write_text(
                'STOCKANALYSIS_DATABASE_URL="postgresql://user:pw@localhost/db"\n',
                encoding="utf-8",
            )
            (runtime_path / "data-operations.env").write_text(
                f'STOCKANALYSIS_DATA_OPERATIONS_ARTIFACT_ROOT="{artifact_root}"\n',
                encoding="utf-8",
            )

            report = build_local_first_runtime_status_report(
                repo_root=repo_root,
                runtime_root=runtime_path,
                url_probe=_next_unreachable_probe,
            )

            next_component = _component(report, "next_cockpit")
            self.assertEqual(next_component["status"], "unreachable")
            self.assertIn("start Next.js cockpit", " ".join(report["next_actions"]))
            self.assertEqual(report["overall_status"], "needs_attention")

    def test_probe_blocked_does_not_claim_service_is_down(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as runtime_root:
            runtime_path = Path(runtime_root)
            artifact_root = runtime_path / "artifacts"
            artifact_root.mkdir()
            (runtime_path / "frontend-api.env").write_text(
                'STOCKANALYSIS_DATABASE_URL="postgresql://user:pw@localhost/db"\n',
                encoding="utf-8",
            )
            (runtime_path / "data-operations.env").write_text(
                f'STOCKANALYSIS_DATA_OPERATIONS_ARTIFACT_ROOT="{artifact_root}"\n',
                encoding="utf-8",
            )

            report = build_local_first_runtime_status_report(
                repo_root=repo_root,
                runtime_root=runtime_path,
                url_probe=_probe_blocked,
            )

            self.assertEqual(_component(report, "frontend_api_live")["status"], "probe_blocked")
            self.assertEqual(_component(report, "next_cockpit")["status"], "probe_blocked")
            self.assertEqual(report["overall_status"], "ready")
            self.assertNotIn("start FastAPI", " ".join(report["next_actions"]))
            self.assertNotIn("start Next.js", " ".join(report["next_actions"]))

    def test_repo_inside_env_file_is_security_risk(self) -> None:
        with tempfile.TemporaryDirectory() as repo_root, tempfile.TemporaryDirectory() as runtime_root:
            repo_path = Path(repo_root)
            repo_env = repo_path / "frontend-api.env"
            repo_env.write_text('STOCKANALYSIS_DATABASE_URL="postgresql://user:pw@localhost/db"\n', encoding="utf-8")

            report = build_local_first_runtime_status_report(
                repo_root=repo_path,
                runtime_root=runtime_root,
                frontend_api_env_file=repo_env,
                skip_http_probes=True,
            )

            component = _component(report, "frontend_api_env_file")
            self.assertEqual(component["status"], "security_risk")
            self.assertEqual(report["overall_status"], "blocked")


def _component(report: dict[str, object], component_name: str) -> dict[str, object]:
    for component in report["components"]:
        if component["component"] == component_name:
            return component
    raise AssertionError(f"Missing component: {component_name}")


def _ok_probe(url: str, timeout_seconds: float) -> dict[str, object]:
    return {"ok": True, "status": "ok", "status_code": 200, "error": ""}


def _next_unreachable_probe(url: str, timeout_seconds: float) -> dict[str, object]:
    if url.endswith("/data-health"):
        return {"ok": False, "status": "unreachable", "status_code": 0, "error": "connection_refused"}
    return {"ok": True, "status": "ok", "status_code": 200, "error": ""}


def _probe_blocked(url: str, timeout_seconds: float) -> dict[str, object]:
    return {"ok": False, "status": "probe_blocked", "status_code": 0, "error": "local_network_permission_denied"}


if __name__ == "__main__":
    unittest.main()
