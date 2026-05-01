# Event Instrument Impact Bootstrap Implementation Plan

**Goal:** pending SEC events를 canonical instrument에 연결하는 첫 bootstrap pipeline을 `event.event_instrument_impact`까지 연다.

**Architecture:** 기존 SEC event rows를 source of truth로 재사용하고, instrument impact가 없는 SEC events를 찾은 뒤 event title/summary에서 company name을 추출한다. 그 이름을 `ref.issuer`와 `ref.instrument`에 exact match로 대조해 canonical instrument를 찾고, 기본 impact 값과 함께 `event.event_instrument_impact`를 upsert한다. 현재 범위는 deterministic exact-match bootstrap only다.

**Tech Stack:** Python 3, Postgres via `psql`, unittest, Docker verification scripts

---

### Task 1: Candidate와 lookup SQL 추가

**Files:**
- Modify: `/Users/woody/ai/stockanalysis/src/stockanalysis/ingest/sec/models.py`
- Modify: `/Users/woody/ai/stockanalysis/src/stockanalysis/ingest/sec/sql.py`
- Test: `/Users/woody/ai/stockanalysis/tests/test_sec_instrument_impact.py`

**Steps:**
- pending SEC event instrument candidates를 위한 model과 SQL을 추가한다.
- canonical instrument exact-match lookup SQL을 추가한다.
- instrument impact upsert SQL을 추가한다.
- unit test로 candidate discovery, lookup SQL, upsert SQL을 고정한다.

### Task 2: Bootstrap runner와 CLI 구현

**Files:**
- Create: `/Users/woody/ai/stockanalysis/src/stockanalysis/ingest/sec/instrument_impact.py`
- Modify: `/Users/woody/ai/stockanalysis/src/stockanalysis/ingest/cli.py`
- Modify: `/Users/woody/ai/stockanalysis/tests/test_ingest_cli.py`
- Test: `/Users/woody/ai/stockanalysis/tests/test_sec_instrument_impact.py`

**Steps:**
- pending SEC event discovery를 runner에 연결한다.
- company name extraction 규칙을 추가한다.
- exact instrument lookup과 impact upsert를 수행한다.
- pipeline run lifecycle과 continue-on-error summary를 추가한다.
- `event-instrument-impact-bootstrap` CLI를 연결한다.

### Task 3: Integration verify와 docs 추가

**Files:**
- Create: `/Users/woody/ai/stockanalysis/scripts/verify_event_instrument_impact_bootstrap.sh`
- Create: `/Users/woody/ai/stockanalysis/docs/event-instrument-impact-bootstrap.md`
- Create: `/Users/woody/ai/stockanalysis/docs/tasks/event-instrument-impact-bootstrap/contract.md`
- Create: `/Users/woody/ai/stockanalysis/docs/tasks/event-instrument-impact-bootstrap/plan.md`
- Create: `/Users/woody/ai/stockanalysis/docs/tasks/event-instrument-impact-bootstrap/handoff.md`
- Create: `/Users/woody/ai/stockanalysis/docs/tasks/event-instrument-impact-bootstrap/review.md`
- Modify: `/Users/woody/ai/stockanalysis/README.md`
- Modify: `/Users/woody/ai/stockanalysis/docs/verification-plan.md`

**Steps:**
- docker-based verify script를 추가한다.
- verify 안에서 canonical Apple issuer/instrument row를 직접 삽입한다.
- annual/quarterly SEC events 2건이 AAPL instrument impact로 연결되는지 검증한다.
- 운영 문서와 handoff를 마무리한다.
