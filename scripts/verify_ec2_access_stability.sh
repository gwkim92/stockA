#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
cd "$ROOT_DIR"

EC2_HOST=${STOCKANALYSIS_EC2_HOST:-3.211.40.142}
EC2_USER=${STOCKANALYSIS_EC2_USER:-ec2-user}
EC2_KEY_PATH=${STOCKANALYSIS_EC2_KEY_PATH:-/Users/woody/Downloads/settle.pem}
EC2_APP_DIR=${STOCKANALYSIS_EC2_APP_DIR:-/opt/stockanalysis/app}
REMOTE_API_URL=${STOCKANALYSIS_EC2_FRONTEND_API_URL:-http://127.0.0.1:8787}
LOCAL_WEB_URL=${STOCKANALYSIS_LOCAL_WEB_URL:-http://127.0.0.1:13000}
REQUIRE_LOCAL_TUNNEL=${STOCKANALYSIS_REQUIRE_LOCAL_TUNNEL:-0}

if [ ! -f "$EC2_KEY_PATH" ]; then
  echo "missing ssh key: $EC2_KEY_PATH" >&2
  exit 1
fi

SSH_OPTS=(
  -i "$EC2_KEY_PATH"
  -o BatchMode=yes
  -o ConnectTimeout=10
  -o ServerAliveInterval=5
  -o ServerAliveCountMax=2
)

ssh "${SSH_OPTS[@]}" "${EC2_USER}@${EC2_HOST}" \
  "EC2_APP_DIR='$EC2_APP_DIR' REMOTE_API_URL='$REMOTE_API_URL' bash -s" <<'REMOTE'
set -euo pipefail

cd "$EC2_APP_DIR"

echo "ec2_branch=$(git rev-parse --abbrev-ref HEAD)"
echo "ec2_commit=$(git rev-parse --short HEAD)"
echo "web_service=$(systemctl is-active stockanalysis-web.service)"
echo "frontend_api_service=$(systemctl is-active stockanalysis-frontend-api.service)"

curl -fsS "$REMOTE_API_URL/__ready" >/tmp/stockanalysis_frontend_api_ready.json
python3 - <<'PY'
import json
from pathlib import Path

payload = json.loads(Path("/tmp/stockanalysis_frontend_api_ready.json").read_text())
runtime = payload.get("runtime") or {}
print(f"api_ready_status={payload.get('status')}")
print(f"api_source_mode={runtime.get('source_mode')}")
print(f"api_auth_mode={runtime.get('auth_mode')}")
print(f"api_order_boundary={runtime.get('order_boundary')}")
PY

set -a
. /opt/stockanalysis/runtime/frontend-api.env
set +a

curl -fsS -H "Authorization: Bearer ${STOCKANALYSIS_FRONTEND_API_READ_TOKEN}" \
  "$REMOTE_API_URL/api/data-health" >/tmp/stockanalysis_data_health.json
python3 - <<'PY'
import json
from pathlib import Path

payload = json.loads(Path("/tmp/stockanalysis_data_health.json").read_text())
data = payload.get("data") or {}
runner = data.get("data_operations_artifact_runner") or {}
ai = data.get("live_ai_invocation_health") or {}
auth = data.get("auth_rbac") or {}
broker_submit_allowed = data.get("broker_submit_allowed")
if broker_submit_allowed is None:
    broker_submit_allowed = auth.get("broker_submit_allowed")
order_boundary = data.get("order_boundary") or auth.get("order_boundary")
print(f"data_health_overall={data.get('overall_status')}")
print("data_health_open_gates=" + ",".join(data.get("open_gates") or []))
print(f"artifact_runner_status={runner.get('status')}")
print(f"artifact_runner_attention={runner.get('attention_required')}")
print(f"live_ai_status={ai.get('status')}")
print(f"auth_rbac_status={auth.get('status')}")
print(f"broker_submit_allowed={broker_submit_allowed}")
print(f"order_boundary={order_boundary}")
PY
REMOTE

if [ "$REQUIRE_LOCAL_TUNNEL" = "1" ]; then
  curl -fsS "$LOCAL_WEB_URL/" >/tmp/stockanalysis_local_web_home.html
  python3 - <<'PY'
from pathlib import Path

html = Path("/tmp/stockanalysis_local_web_home.html").read_text(errors="replace")
print(f"local_web_bytes={len(html)}")
print(f"local_web_has_html={'<html' in html.lower()}")
PY
fi

echo "ec2 access stability verification passed"
