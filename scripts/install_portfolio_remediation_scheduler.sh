#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
MODE="--dry-run"
LABEL="${PORTFOLIO_REMEDIATION_LAUNCHD_LABEL:-com.stockanalysis.portfolio-remediation-daily}"
HOUR="${PORTFOLIO_REMEDIATION_SCHEDULE_HOUR:-18}"
MINUTE="${PORTFOLIO_REMEDIATION_SCHEDULE_MINUTE:-30}"
ARTIFACT_ROOT="${PORTFOLIO_REMEDIATION_INSTALL_ARTIFACT_ROOT:-$ROOT_DIR/artifacts/portfolio-remediation-scheduler/install}"
ENV_FILE="${PORTFOLIO_REMEDIATION_ENV_FILE:-}"
WRAPPER_PATH="$ROOT_DIR/scripts/run_portfolio_remediation_daily_scheduler.sh"
HOST_PLIST_DIR="${HOME:-}/Library/LaunchAgents"

usage() {
  cat <<'USAGE'
Usage:
  scripts/install_portfolio_remediation_scheduler.sh [--dry-run|--install] --env-file PATH

Environment overrides:
  PORTFOLIO_REMEDIATION_LAUNCHD_LABEL
  PORTFOLIO_REMEDIATION_SCHEDULE_HOUR
  PORTFOLIO_REMEDIATION_SCHEDULE_MINUTE
  PORTFOLIO_REMEDIATION_INSTALL_ARTIFACT_ROOT
USAGE
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --dry-run)
      MODE="--dry-run"
      shift
      ;;
    --install)
      MODE="--install"
      shift
      ;;
    --env-file)
      if [ "$#" -lt 2 ]; then
        echo "--env-file requires a path." >&2
        exit 2
      fi
      ENV_FILE="$2"
      shift 2
      ;;
    --help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [ -z "$ENV_FILE" ]; then
  echo "Missing required --env-file PATH." >&2
  exit 1
fi

if [ ! -f "$ENV_FILE" ]; then
  echo "Env file does not exist: $ENV_FILE" >&2
  exit 1
fi

if [ ! -x "$WRAPPER_PATH" ]; then
  echo "Scheduler wrapper is missing or not executable: $WRAPPER_PATH" >&2
  exit 1
fi

case "$HOUR" in
  ""|*[!0-9]*)
    echo "PORTFOLIO_REMEDIATION_SCHEDULE_HOUR must be an integer." >&2
    exit 1
    ;;
esac

case "$MINUTE" in
  ""|*[!0-9]*)
    echo "PORTFOLIO_REMEDIATION_SCHEDULE_MINUTE must be an integer." >&2
    exit 1
    ;;
esac

if [ "$HOUR" -lt 0 ] || [ "$HOUR" -gt 23 ]; then
  echo "PORTFOLIO_REMEDIATION_SCHEDULE_HOUR must be between 0 and 23." >&2
  exit 1
fi

if [ "$MINUTE" -lt 0 ] || [ "$MINUTE" -gt 59 ]; then
  echo "PORTFOLIO_REMEDIATION_SCHEDULE_MINUTE must be between 0 and 59." >&2
  exit 1
fi

mkdir -p "$ARTIFACT_ROOT"
if [ ! -w "$ARTIFACT_ROOT" ]; then
  echo "Install artifact root is not writable: $ARTIFACT_ROOT" >&2
  exit 1
fi

PLIST_PATH="$ARTIFACT_ROOT/$LABEL.plist"
STDOUT_LOG="$ARTIFACT_ROOT/$LABEL.stdout.log"
STDERR_LOG="$ARTIFACT_ROOT/$LABEL.stderr.log"

python3 - "$PLIST_PATH" "$LABEL" "$ROOT_DIR" "$WRAPPER_PATH" "$ENV_FILE" "$STDOUT_LOG" "$STDERR_LOG" "$HOUR" "$MINUTE" <<'PY'
import plistlib
import shlex
import sys

plist_path, label, root_dir, wrapper_path, env_file, stdout_log, stderr_log, hour, minute = sys.argv[1:]

calendar = [
    {"Weekday": weekday, "Hour": int(hour), "Minute": int(minute)}
    for weekday in range(2, 7)
]
payload = {
    "Label": label,
    "ProgramArguments": [
        "/bin/bash",
        "-lc",
        f"set -a; . {shlex.quote(env_file)}; set +a; exec /bin/bash {shlex.quote(wrapper_path)}",
    ],
    "WorkingDirectory": root_dir,
    "StartCalendarInterval": calendar,
    "StandardOutPath": stdout_log,
    "StandardErrorPath": stderr_log,
    "RunAtLoad": False,
}

with open(plist_path, "wb") as handle:
    plistlib.dump(payload, handle, sort_keys=False)
PY

if [ "$MODE" = "--dry-run" ]; then
  echo "$PLIST_PATH"
  exit 0
fi

if [ -z "${HOME:-}" ]; then
  echo "HOME is required for --install." >&2
  exit 1
fi

mkdir -p "$HOST_PLIST_DIR"
HOST_PLIST_PATH="$HOST_PLIST_DIR/$LABEL.plist"
cp "$PLIST_PATH" "$HOST_PLIST_PATH"

cat <<EOF
Installed launchd plist:
$HOST_PLIST_PATH

Manual activation command:
launchctl bootstrap gui/$(id -u) "$HOST_PLIST_PATH"

Manual deactivation command:
launchctl bootout gui/$(id -u) "$HOST_PLIST_PATH"
EOF
