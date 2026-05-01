# Portfolio Review Coverage Gate Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Portfolio review가 requested outcome coverage blind spot을 review action과 risk에 반영하게 만든다.

**Architecture:** 기존 `portfolio-review-bootstrap` candidate lookup에 선택적 `coverage_measurement_end_date`를 추가한다. 옵션이 없으면 기존 동작을 유지하고, 옵션이 있으면 position-linked thesis와 `performance.thesis_outcome`을 left join해 `covered`, `missing_outcome`, `missing_thesis`, `missing_weight`를 review item action/risk/summary에 반영한다.

**Tech Stack:** Python stdlib, argparse CLI, Postgres SQL, existing psql executor, Docker verification script.

---

### Task 1: Harness

**Files:**
- Create: `docs/tasks/portfolio-review-coverage-gate/contract.md`
- Create: `docs/tasks/portfolio-review-coverage-gate/plan.md`
- Create: `docs/tasks/portfolio-review-coverage-gate/handoff.md`
- Create: `docs/tasks/portfolio-review-coverage-gate/review.md`

**Steps:**
- optional coverage gate scope를 문서화한다.
- 기존 review 동작이 옵션 없을 때 유지되어야 함을 명시한다.
- 검증 명령과 Docker 기대값을 명시한다.

### Task 2: Portfolio Review Model And SQL

**Files:**
- Modify: `src/stockanalysis/signal/portfolio_review.py`
- Test: `tests/test_portfolio_review_bootstrap.py`

**Steps:**
- `PortfolioReviewCandidate`에 `coverage_measurement_end_date`, `coverage_status`, `outcome_id`, `outcome_status`, `outcome_success_grade`를 추가한다.
- `render_portfolio_review_candidate_lookup_sql`에 optional measurement end date를 추가한다.
- measurement date가 없으면 `coverage_status`는 `not_requested`로 둔다.
- measurement date가 있으면 position-linked thesis 기준으로 `missing_thesis`, `missing_weight`, `missing_outcome`, `covered`를 계산한다.

### Task 3: Review Action Gate

**Files:**
- Modify: `src/stockanalysis/signal/portfolio_review.py`
- Test: `tests/test_portfolio_review_bootstrap.py`

**Steps:**
- `missing_thesis`는 `needs_thesis_review`로 매핑한다.
- `missing_outcome`은 새 action `needs_outcome_review`로 매핑한다.
- `missing_weight`는 새 action `needs_weight_review`로 매핑한다.
- 새 gate action은 priority 3, risk `watch`로 둔다.
- reason과 overall summary에 coverage status를 포함한다.

### Task 4: CLI And Integration Verify

**Files:**
- Modify: `src/stockanalysis/ingest/cli.py`
- Modify: `tests/test_ingest_cli.py`
- Modify: `scripts/verify_portfolio_review_bootstrap.sh`

**Steps:**
- `portfolio-review-bootstrap`에 `--coverage-measurement-end-date` 옵션을 추가한다.
- CLI handler가 optional date를 runner에 전달한다.
- Docker verify에서 coverage gap fixture를 쓰는 second review run을 추가한다.
- BABA review item이 `needs_thesis_review`이고 header risk가 `watch`인지 확인한다.

### Task 5: Docs And Final Verification

**Files:**
- Modify: `README.md`
- Modify: `docs/portfolio-review-bootstrap.md`
- Modify: `docs/portfolio-outcome-coverage-report.md`
- Modify: `docs/verification-plan.md`
- Modify: `docs/tasks/portfolio-review-coverage-gate/handoff.md`
- Modify: `docs/tasks/portfolio-review-coverage-gate/review.md`

**Steps:**
- coverage gate usage와 boundary를 문서화한다.
- compileall, full unittest, shell syntax, Docker verify, harness verify, placeholder search를 실행한다.
