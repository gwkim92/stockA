# ai-batch-provider-fallback-hardening-v1 Contract

## Purpose

OpenAI paid API quota가 부족해도 batch AI 운영이 멈추지 않도록 `agents_sdk_openai -> codex_oauth -> local_rules` fallback 상태를 추적 가능하게 만들고, 운영 smoke CLI가 일관된 env-file 인자를 받게 한다.

## Task Request

- request: OpenAI paid quota 부족 상태에서도 운영자가 AI agent registry, provider health, fallback 경로를 같은 env-file 기반 CLI smoke로 확인할 수 있게 한다.

`ai-batch-provider-fallback-hardening-v1`: OpenAI paid quota 부족 상태에서도 운영자가 AI agent registry, provider health, fallback 경로를 같은 env-file 기반 CLI smoke로 확인할 수 있게 한다.

## Goal

- goal: `stockanalysis-operations ai-agent-registry-report --env-file <ENV> --repo-root <ROOT>`가 secret을 출력하지 않으면서 실행되고, EC2에서 `codex_oauth`와 `local_rules` fallback 상태가 확인된다.

`stockanalysis-operations ai-agent-registry-report --env-file <ENV> --repo-root <ROOT>`가 secret을 출력하지 않으면서 실행되고, EC2에서 `codex_oauth`와 `local_rules` fallback 상태가 확인된다.

## Mutable Surface

- mutable surface:
  - `src/stockanalysis/operations/cli.py`
  - `src/stockanalysis/operations/env_readiness.py`
  - `tests/test_data_operations_cli.py`
  - `docs/tasks/ai-batch-provider-fallback-hardening-v1/`

- `src/stockanalysis/operations/cli.py`
- `src/stockanalysis/operations/env_readiness.py`
- `tests/test_data_operations_cli.py`
- `docs/tasks/ai-batch-provider-fallback-hardening-v1/`

## Scope

- `ai-agent-registry-report`
- `openai-provider-health-report`
- `/api/data-health.live_ai_invocation_health`
- `/api/data-health.openai_provider_health`

## Rules

- OpenAI quota 부족은 결제로 해결하지 않는다.
- Codex OAuth와 local rules fallback을 기본 복구 경로로 유지한다.
- 실패한 invocation은 삭제하지 않는다. 최신 성공 invocation과 run history로 자연스럽게 이어붙인다.
- AI는 추천이나 주문을 직접 결정하지 않는다.
- Broker submit과 automatic order는 계속 금지한다.

## Deliverables

- `stockanalysis-operations ai-agent-registry-report --env-file <ENV> --repo-root <ROOT>` 호환.
- Secret-free AI provider/fallback visibility evidence.
- Task handoff.

## Verification

- verification command: `PYTHONPATH=src python3 -m unittest tests.test_data_operations_cli tests.test_frontend_live_adapter`
- verification command: `PYTHONPATH=src python3 -m compileall -q src tests`
- verification command: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task ai-batch-provider-fallback-hardening-v1`

```bash
PYTHONPATH=src python3 -m unittest tests.test_data_operations_cli.DataOperationsCliTests.test_ai_agent_registry_report_accepts_repo_outside_env_without_secrets
PYTHONPATH=src python3 -m unittest tests.test_data_operations_cli.DataOperationsCliTests.test_openai_provider_health_report_is_secret_free_and_reads_cached_status
PYTHONPATH=src python3 -m unittest tests.test_data_operations_cli tests.test_frontend_live_adapter
PYTHONPATH=src python3 -m compileall -q src tests
```
