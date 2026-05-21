#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
cd "$ROOT_DIR"

bash -n scripts/verify_operating_data_profile_scheduler_invocation.sh
python3 -m compileall \
  src/stockanalysis/operations/operating_data_profile_scheduler.py \
  src/stockanalysis/operations/cli.py \
  tests/test_operating_data_profile_scheduler.py \
  tests/test_data_operations_cli.py >/dev/null

PYTHONPATH=src python3 -m unittest \
  tests.test_operating_data_profile_scheduler \
  tests.test_data_operations_cli.DataOperationsCliTests.test_operating_data_profile_scheduler_invocation_plan_command_writes_output_and_markdown \
  tests.test_data_operations_cli.DataOperationsCliTests.test_operating_data_profile_scheduler_invocation_plan_rejects_repo_inside_output \
  tests.test_data_operations_cli.DataOperationsCliTests.test_operating_data_profile_scheduler_invocation_plan_rejects_repo_inside_manifest_output_root >/dev/null

TMP_ROOT=$(mktemp -d /tmp/stockanalysis-operating-data-profile-scheduler.XXXXXX)
trap 'rm -rf "$TMP_ROOT"' EXIT

mkdir -p "$TMP_ROOT/artifacts" "$TMP_ROOT/runtime" "$TMP_ROOT/reports" "$TMP_ROOT/manifests"
cat >"$TMP_ROOT/data-operations.env" <<EOF
STOCKANALYSIS_DATABASE_URL="postgresql://user:hidden-verifier-pass@localhost/db"
STOCKANALYSIS_DATA_OPERATIONS_ARTIFACT_ROOT="$TMP_ROOT/artifacts"
EOF

PYTHONPATH=src python3 -m stockanalysis.operations.cli operating-data-profile-scheduler-invocation-plan \
  --repo-root "$ROOT_DIR" \
  --target cron \
  --runtime-root "$TMP_ROOT/runtime" \
  --data-operations-env-file "$TMP_ROOT/data-operations.env" \
  --profile-output-root "$TMP_ROOT/reports" \
  --manifest-output-root "$TMP_ROOT/manifests" \
  --profile-id news-intraday \
  --profile-id market-daily \
  --execute \
  --output "$TMP_ROOT/operating-data-profile-scheduler.json" \
  --markdown-output "$TMP_ROOT/operating-data-profile-scheduler.md" >/dev/null

python3 - "$TMP_ROOT/operating-data-profile-scheduler.json" "$TMP_ROOT/operating-data-profile-scheduler.md" <<'PY'
import json
import os
import sys

report_path, markdown_path = sys.argv[1], sys.argv[2]
text = open(report_path, encoding="utf-8").read()
markdown = open(markdown_path, encoding="utf-8").read()
payload = json.loads(text)

assert payload["report_name"] == "operating_data_profile_scheduler_invocation_boundary"
assert payload["scheduler_target"] == "cron"
assert payload["include_full_recovery"] is False
assert payload["operating_data_run_execute"] is True
assert payload["total_profile_count"] == 2
assert payload["manifest_output_root"].endswith("/manifests")
assert os.path.isabs(payload["manifest_output_root"]), payload["manifest_output_root"]
assert os.path.isdir(payload["manifest_output_root"]), payload["manifest_output_root"]
assert payload["profiles"][0]["profile_id"] == "news-intraday"
assert payload["profiles"][1]["profile_id"] == "market-daily"
assert "--execute" in payload["profiles"][0]["command_argv_preview"]
assert payload["profiles"][0]["manifest_file_previews"]
assert payload["profiles"][1]["manifest_file_previews"]
for profile in payload["profiles"]:
    for manifest_file in profile["manifest_file_previews"]:
        assert manifest_file["path"] != ""
        assert open(manifest_file["path"], encoding="utf-8").read() is not None
assert payload["manifest_records"]
assert payload["manifest_records"][0]["manifest"]["target"] in ("cron", "systemd", "kubernetes_cronjob", "managed_scheduler")
assert "0 0 * * *" not in text
assert "hidden-verifier-pass" not in text + markdown
assert "postgresql://" not in text + markdown
assert "Operating Data Profile Scheduler Invocation Boundary" in markdown
assert "/manifests" in markdown
print("operating data profile scheduler invocation verification passed")
PY

PYTHONPATH=src python3 -m stockanalysis.operations.cli operating-data-profile-scheduler-invocation-plan \
  --repo-root "$ROOT_DIR" \
  --target systemd \
  --runtime-root "$TMP_ROOT/runtime" \
  --data-operations-env-file "$TMP_ROOT/data-operations.env" \
  --profile-output-root "$TMP_ROOT/reports-systemd" \
  --manifest-output-root "$TMP_ROOT/manifests-systemd" \
  --python-executable "$TMP_ROOT/runtime/venv/bin/python" \
  --execute \
  --output "$TMP_ROOT/operating-data-profile-scheduler-systemd.json" >/dev/null

python3 - "$TMP_ROOT/operating-data-profile-scheduler-systemd.json" <<'PY'
import json
import pathlib
import sys

payload = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
assert payload["scheduler_target"] == "systemd"
assert payload["operating_data_run_execute"] is True
assert payload["total_profile_count"] == 5
timer_text = "\n".join(
    pathlib.Path(item["path"]).read_text(encoding="utf-8")
    for profile in payload["profiles"]
    for item in profile["manifest_file_previews"]
    if item["kind"] == "systemd_timer"
)
assert "OnCalendar=Mon..Fri *-*-* 09..18:00/30 America/New_York" in timer_text
assert "OnCalendar=Mon..Fri *-*-* 18:35 America/New_York" in timer_text
assert "OnCalendar=Mon..Fri *-*-* 19:00 America/New_York" in timer_text
assert "OnCalendar=*-*-01 09:30 America/New_York" in timer_text
assert "--execute" in json.dumps(payload)
print("operating data profile systemd manifest verification passed")
PY
