#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
DDL_VERIFY_INCLUDE_SEEDS=1 bash "$ROOT_DIR/scripts/verify_migrations.sh"
