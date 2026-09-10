from __future__ import annotations

import importlib
import json
import os
import subprocess
import tempfile
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

from stockanalysis.ai.model_settings import CodexModelInvocation, ModelSettingsStore, PATH_ENV, SettingsError, WORKLOADS
from stockanalysis.frontend.api_server import create_app
from stockanalysis.frontend.runtime_policy import FrontendRuntimePolicy


class ModelSettingsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = ModelSettingsStore(Path(self.temp.name) / "settings.sqlite3")
        self.store.initialize("gpt-5.6-terra")
        self.store.set_catalog([{"id": "gpt-5.6-terra"}, {"id": "gpt-5.6-luna"}, {"id": "internal", "hidden": True}])
        self.session = self.store.claim_code(self.store.issue_code())
        self.env = patch.dict(os.environ, {PATH_ENV: str(self.store.path), "STOCKANALYSIS_CODEX_CLI_COMMAND": "codex -c model=gpt-5.6-terra"})
        self.env.start()
        self.addCleanup(self.env.stop)

    def change(self, **kwargs):
        return {"revision": 0, "default_model": "gpt-5.6-luna", "overrides": {}, **kwargs}

    def test_authentication_replay_expiry_and_no_secrets_in_inventory(self):
        code = self.store.issue_code()
        session = self.store.claim_code(code)
        with self.assertRaises(SettingsError): self.store.claim_code(code)
        self.assertTrue(self.store.read(session)["authorized"])
        raw = json.dumps(self.store.read(session))
        self.assertNotIn(session, raw)
        self.assertNotIn(code, raw)
        self.assertNotIn("internal", raw)
        self.assertEqual(self.store.path.stat().st_mode & 0o777, 0o600)
        self.store.revoke(session)
        with self.assertRaises(SettingsError): self.store.update(self.change(), session)
        with self.store.connect() as db: db.execute("update sessions set expires_at=?", (time.time() - 1,))
        with self.assertRaises(SettingsError): self.store.update(self.change(), self.session)

    def test_atomic_conflict_persistence_audit_and_allowlist(self):
        for payload in [self.change(default_model="model;touch /tmp/no"), self.change(overrides={"unknown": "gpt-5.6-luna"}), self.change(overrides={WORKLOADS[0][0]: ["bad"]})]:
            with self.assertRaises(SettingsError): self.store.update(payload, self.session)
        def update():
            try: return self.store.update(self.change(), self.session)["revision"]
            except SettingsError as exc: return exc.status
        with ThreadPoolExecutor(max_workers=2) as pool: results = list(pool.map(lambda _: update(), range(2)))
        self.assertCountEqual(results, [1, 409])
        readback = ModelSettingsStore(self.store.path).read()
        self.assertEqual(readback["default_model"], "gpt-5.6-luna")
        self.assertEqual(len(readback["audit"]), 1)
        self.assertEqual(readback["audit"][0]["before"]["default_model"], "gpt-5.6-terra")

    def test_settings_snapshot_explicit_override_and_failed_attempt(self):
        task = WORKLOADS[0][0]
        with CodexModelInvocation(task, "codex-cli-default") as old:
            self.store.update(self.change(overrides={task: "gpt-5.6-terra"}), self.session)
            self.assertEqual(old.model, "gpt-5.6-terra")
            self.assertEqual(old.revision, 0)
        with CodexModelInvocation(WORKLOADS[1][0], "codex-cli-default") as inherited:
            self.assertEqual(inherited.model, "gpt-5.6-luna")
        with CodexModelInvocation(task, "gpt-5.6-luna") as explicit:
            self.assertEqual(explicit.model, "gpt-5.6-luna")
            explicit.run(lambda: subprocess.CompletedProcess([], 0, "", "model: gpt-5.6-luna\nreasoning effort: none\nuser\nmodel: fake"))
        with self.assertRaises(ValueError):
            with CodexModelInvocation(task, "codex-cli-default"):
                raise ValueError("invalid generated output token=must-not-leak")
        result = self.store.read()["workloads"][0]
        self.assertEqual(result["latest"]["status"], "failed")
        self.assertEqual(result["last_success"]["actual_model"], "gpt-5.6-luna")
        self.assertNotIn("must-not-leak", json.dumps(result))

    def test_read_token_cannot_write_and_scoped_session_can(self):
        policy = FrontendRuntimePolicy(profile="local", source="fixture", auth_mode="read-token", read_token="test-read")
        with TestClient(create_app(runtime_policy=policy)) as client:
            headers = {"Authorization": "Bearer test-read"}
            self.assertEqual(client.get("/__admin/model-settings").status_code, 401)
            self.assertEqual(client.get("/__admin/model-settings", headers=headers).status_code, 200)
            self.assertEqual(client.patch("/__admin/model-settings", headers=headers, json=self.change()).status_code, 403)
            code = self.store.issue_code()
            login = client.post("/__admin/model-settings/session", headers=headers, json={"code": code})
            self.assertEqual(login.status_code, 200)
            headers["X-Stockanalysis-Model-Session"] = login.json()["session"]
            self.assertEqual(client.patch("/__admin/model-settings", headers=headers, json=self.change()).status_code, 200)
            self.assertEqual(client.patch("/__admin/model-settings", headers=headers, json=self.change()).status_code, 409)
            self.assertEqual(client.post("/api/orders", headers=headers, json={}).status_code, 405)
            self.assertEqual(client.delete("/__admin/model-settings/session", headers=headers).status_code, 200)
            self.assertEqual(client.patch("/__admin/model-settings", headers=headers, json=self.change(revision=1)).status_code, 403)

    def test_all_five_adapters_apply_saved_model_and_trust_cli_metadata(self):
        self.store.update(self.change(), self.session)
        cases = [
            ("ingest.news.translation", "invoke_codex_oauth_news_translation_provider", "build_codex_oauth_news_translation_prompt", "build_news_translation_provider_response_from_payload", (SimpleNamespace(), "text", "codex-cli-default", "low")),
            ("ingest.news.ai_extract", "invoke_codex_oauth_news_ai_provider", "build_codex_oauth_news_ai_prompt", "build_news_ai_provider_response_from_payload", (SimpleNamespace(title="test", summary="test"), SimpleNamespace(token_count=1), {}, "codex-cli-default", "low")),
            ("ai.cycle_community_ai_summary", "invoke_codex_oauth_cycle_community_ai_provider", "build_codex_oauth_cycle_community_ai_prompt", "parse_cycle_community_ai_response_payload", ({}, "codex-cli-default", "low", 10000)),
            ("ai.equity_research_reporting", "invoke_codex_oauth_equity_research_provider", "build_codex_oauth_equity_research_prompt", "parse_equity_research_response_payload", ({}, "codex-cli-default", "low", 10000)),
            ("ingest.sec.ai_event_extract", "invoke_codex_oauth_structured_event_provider", "build_codex_oauth_event_prompt", "build_structured_event_provider_response_from_payload", (SimpleNamespace(), SimpleNamespace(token_count=1), "codex-cli-default", "low")),
        ]
        parsed = SimpleNamespace(model_name="generated-fake-model", reasoning_effort="high", output=SimpleNamespace(evidence_spans=[]), event=SimpleNamespace(), input_token_count=1, output_token_count=1, cached_input_token_count=0, estimated_cost_usd=0, latency_ms=1)
        def fake_run(command, **kwargs):
            self.assertEqual(command[command.index("--model") + 1], "gpt-5.6-luna")
            Path(command[command.index("--output-last-message") + 1]).write_text("{}")
            return subprocess.CompletedProcess(command, 0, "", "model: gpt-5.6-luna\nreasoning effort: none\n")
        for module_name, function, prompt, parser, args in cases:
            with self.subTest(module=module_name):
                module = importlib.import_module("stockanalysis." + module_name)
                with patch.object(module, prompt, return_value="bounded prompt"), patch.object(module, parser, return_value=parsed), patch.object(module.subprocess, "run", side_effect=fake_run):
                    response = getattr(module, function)(*args)
                    self.assertEqual(response.model_name, "gpt-5.6-luna")
                    self.assertEqual(response.reasoning_effort, "none")
        self.assertTrue(all(row["last_success"]["actual_model"] == "gpt-5.6-luna" for row in self.store.read()["workloads"]))


if __name__ == "__main__": unittest.main()
