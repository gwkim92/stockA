"""Read-only stockA runtime probe; run on the verified EC2 through stdin."""
import datetime
import json
import os
import subprocess
import urllib.request
from pathlib import Path

from stockanalysis.operations.env_file import load_env_file_values


def get_json(path):
    token = os.environ.get("STOCKANALYSIS_FRONTEND_API_READ_TOKEN", "")
    request = urllib.request.Request(
        "http://127.0.0.1:8787" + path,
        headers={"Authorization": "Bearer " + token},
    )
    with urllib.request.urlopen(request, timeout=40) as response:
        return json.load(response)


os.environ.update(load_env_file_values("/opt/stockanalysis/runtime/frontend-api.env"))
health_response = get_json("/api/data-health")
health = health_response.get("data", health_response)
selected = [
    "overall_status", "open_gates", "open_gate_details", "live_ai_invocation_health",
    "active_recommendation_price_freshness", "market_price_provider_budget",
    "recommendation_outcome_maturity", "outcome_maturity_wait_monitor",
    "recommendation_weight_review_readiness", "recommendation_weight_review_readiness_v2",
    "portfolio_review_feedback_calibration", "portfolio_review_feedback_cadence",
    "portfolio_review_feedback_action_router", "recommendation_outcome_due_action_router",
    "data_operations_artifact_runner", "alert_destination", "professional_analysis_quality",
]
report = {
    "checked_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "health_keys": list(health),
    "health": {key: health[key] for key in selected if key in health},
    "runtime_env_files": sorted(p.name for p in Path("/opt/stockanalysis/runtime").glob("*.env")),
}
oauth = get_json("/__admin/codex-oauth/status")
report["oauth"] = {key: oauth[key] for key in [
    "status", "authenticated", "login_status", "login_probe", "last_smoke_status",
    "last_direct_smoke", "last_news_smoke", "last_error", "action_required",
] if key in oauth}
report["oauth_keys"] = list(oauth)
units = subprocess.run(
    ["systemctl", "list-units", "--all", "--plain", "--no-legend", "stockanalysis-*.service"],
    text=True, capture_output=True, check=True,
).stdout
report["units"] = units
report["market_unit"] = subprocess.run(
    ["systemctl", "show", "stockanalysis-operating-data-market-daily.service",
     "--property=EnvironmentFiles,User,WorkingDirectory,ExecMainStatus,Result"],
    text=True, capture_output=True, check=True,
).stdout
print(json.dumps(report, ensure_ascii=False, indent=2))
