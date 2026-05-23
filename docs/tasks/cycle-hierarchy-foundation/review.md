# Review

## Verification

- Passed:
  - `PYTHONPATH=src /opt/homebrew/bin/python3.13 -m unittest tests.test_cycle_hierarchy_seed tests.test_ai_ontology_validation tests.test_macro_event_propagation` - 16 tests OK
  - `git diff --check` - OK
  - `bash scripts/verify_seed_bootstrap.sh` - Docker Postgres migrations/seeds applied; `ref.classification_node=11`, `ref.classification_edge=17`, `ref.instrument_factor_exposure=18`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src /private/tmp/stockanalysis-runtime/verify-venv/bin/python -m awh verify --repo . --task cycle-hierarchy-foundation` - passed readiness checks

## Notes

- EC2 실제 DB에서 `QUBT -> QUANTUM_COMPUTING_POLICY`에 legacy `macro_sensitivity` exposure가 남아 있는 것을 확인했다.
- seed 재적용 시 source document가 없는 해당 legacy row는 제거하고, propagation lookup은 동일 event/node/instrument 후보를 exposure priority로 1개만 선택한다.

## Risks

- 첫 slice는 계층 그래프 foundation만 만든다. AI extract v2, multi-hop propagation, cycle snapshot v2, frontend cycle map은 후속 task에서 구현해야 한다.
- `MACRO_RATES_FED`는 기존 RSS enrichment 호환성을 위해 `subtheme` node_type을 유지한다. 계층 레벨은 후속 `cycle_hierarchy_snapshot_v2`에서 별도 level field로 정규화해야 한다.
