# Task Contract

## Task

- 이름: cycle-hierarchy-foundation
- 요청: 계층형 사이클·뉴스·AI 고도화 계획의 첫 단계로 거시·도메인·테마 ontology-lite foundation을 만든다.
- 담당: Codex
- 날짜: 2026-05-23

## Goal

- 이 작업이 끝났을 때 반드시 참이어야 하는 상태: 빈 DB에 migration과 seed를 적용하면 `거시 흐름 -> 도메인 -> 테마 -> 종목 exposure`의 최소 계층 그래프가 생기고, 후속 AI extract v2, multi-hop propagation, cycle hierarchy snapshot이 이 그래프를 기준으로 동작할 수 있다.

## Scope

- 포함:
  - 최소 거시/도메인/테마 classification node seed
  - macro/domain/theme classification edge seed
  - 핵심 종목 starter factor exposure seed
  - ontology validation allowed relation type 확장
  - seed 검증 테스트와 task 문서
- 제외:
  - AI extract v2 구현
  - multi-hop propagation runner 구현
  - cycle hierarchy snapshot v2 구현
  - recommendation score formula 변경
  - frontend 신규 `/cycle-map` 화면
  - 외부 graph/vector DB 또는 유료 RAG 서비스 도입

## Mutable Surface

- 수정 가능한 파일:
  - `db/seeds/`
  - `src/stockanalysis/ai/ontology_validation.py`
  - `src/stockanalysis/signal/macro_event_propagation.py`
  - `scripts/verify_migrations.sh`
  - `tests/`
  - `docs/tasks/cycle-hierarchy-foundation/`
- 수정 금지 파일:
  - `.env`와 secret 값
  - broker/live order submission
  - benchmark/evaluation split

## Verification

- 검증에 사용할 명령:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_cycle_hierarchy_seed tests.test_ai_ontology_validation tests.test_macro_event_propagation`
  - `bash scripts/verify_seed_bootstrap.sh`
  - `git diff --check`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/verify-venv/bin/python -m awh verify --repo . --task cycle-hierarchy-foundation`

## Done Criteria

- 최소 노드 `MACRO_RATES_FED`, `MACRO_INFLATION`, `MACRO_LIQUIDITY`, `MACRO_GROWTH`, `ENERGY_GEOPOLITICS`, `TECH_DOMAIN`, `AI_SEMICONDUCTOR_CYCLE`, `QUANTUM_COMPUTING_POLICY`가 seed에 존재한다.
- 거시에서 도메인/테마로 이어지는 edge가 idempotent하게 seed된다.
- `QUBT`, `QQQ`, `TLT`, `NVDA` 등 starter exposure가 후속 propagation 입력으로 쓸 수 있게 seed된다.
- ontology validation이 새 relation type을 허용한다.
- 기존 DB에 같은 instrument/node의 legacy exposure가 남아 있어도 propagation candidate가 하나로 정규화된다.
