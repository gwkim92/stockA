# Session Handoff

## Active Task

- 이름: news-dedup-symbol-classification-root-cause
- 담당: Codex
- 날짜: 2026-05-21

## Current Status

- 진행 중:
  - EC2 DB에서 event `11`, `19`가 각각 2개 theme impact를 가져 cluster/API 중복 노출을 만드는 것을 확인했다.
  - frontend event list SQL을 primary theme/instrument lateral 선택으로 바꿨다.
  - news cluster candidate SQL과 cluster builder를 event 단위 primary cluster 구조로 바꿨다.
  - `ref.instrument.name` 기반 company alias lookup을 추가했고 EC2 read-only smoke에서 `ADI`, `INTU`, `TGT` 매칭과 `price target` 오탐 방지를 확인했다.
  - EC2 실행 중 `FINANCIAL INSTITUTIONS INC`가 Fed 문장의 일반어 `financial institutions`에 오탐 매칭되는 것을 발견해 alias blocklist를 추가했다.
  - cluster artifact request hash가 `event_id`만 포함해 symbol correction을 반영하지 못하는 구조를 발견했고, event fingerprint에 symbol/direction/score를 포함하도록 바꿨다.
  - `/api/ai/news-clusters`가 과거 cluster artifact까지 모두 반환해 stale cluster가 화면에 섞일 수 있는 것을 발견했고, theme별 최신 artifact만 노출하도록 SQL superseding 기준을 추가했다.
  - 로컬 관련 테스트와 전체 테스트는 통과했다.

## Exact Next Step

- exact next step: 최신 API superseding 커밋을 EC2에 배포한 뒤 `/api/ai/news-clusters?asOfDate=2026-05-21&limit=4`가 최신 theme cluster 4건만 반환하고 duplicate event id가 없는지 확인한다.

## Root Cause

- EC2 DB에서 `news_rss_item` 중 event `11`, `19`가 각각 2개 theme impact를 가지고 있었다.
- frontend event list SQL이 `event.event`를 `event_classification_impact`와 `event_instrument_impact`에 직접 조인해서 event x theme x instrument 형태로 행이 증폭됐다.
- news cluster evidence 후보 SQL도 같은 직접 조인 구조라 event 하나가 여러 theme cluster에 중복 배치됐다.
- `종목 미분류`는 두 원인이 섞여 있었다.
  - Fed/SEC/채권/세금/시장 구조 뉴스처럼 단일 listed equity에 붙이기 어려운 경우는 정상적인 `symbol 없음`이다.
  - `Analog Devices`, `Intuit`, `Target`처럼 명확한 회사명 뉴스는 기존 `_SYMBOL_KEYWORDS`가 작은 수동 키워드 목록이라 instrument alias를 못 찾았고, AI 후보의 낮은 confidence는 validator threshold 때문에 canonical instrument impact로 반영되지 않았다.

## Changes

- `render_frontend_event_list_state_sql`이 primary instrument/theme impact를 `lateral ... limit 1`로 고르게 변경했다.
- `render_news_rss_cluster_evidence_event_candidates_sql`이 primary theme/instrument만 선택하도록 변경했다.
- `build_news_rss_clusters`가 방어적으로 같은 `event_id`를 한 cluster에만 넣도록 변경했다.
- news RSS enrichment에 `ref.instrument.name` 기반 company alias lookup을 추가했다.
  - multi-word 회사명은 본문/제목에서 정확 phrase를 찾는다.
  - single-word 회사명은 제목 prefix 또는 `{alias} stock` 문맥일 때만 허용한다.
  - `price target` 문맥은 `Target Corp` 오탐을 피하기 위해 제외한다.

## Verification

- EC2 read-only DB check before fix: event `11`, `19`가 duplicate cluster appearances를 만들었다.
- EC2 SQL syntax check after fix:
  - `Analog Devices` -> `ADI`
  - `Intuit` -> `INTU`
  - `Target Names New Supply Chain Chief` -> `TGT`
  - `Analysts lift price target after earnings` -> no match
- EC2 execution check found and fixed alias false positive:
  - generic `financial institutions` no longer resolves to `FISI`.
- `PYTHONPATH=src python3 -m unittest tests.test_news_rss_cluster_evidence tests.test_news_rss_enrichment tests.test_frontend_live_adapter tests.test_news_rss_ai_extract`: pass, 80 tests.
- `PYTHONPATH=src /private/tmp/stockanalysis-runtime/test-venv/bin/python -m unittest discover -s tests`: pass, 700 tests.
- `git diff --check`: pass.

## Remaining Work

- EC2 배포 후 `news_rss_event_enrichment`와 `news_rss_cluster_evidence`를 한 번 실행해 최신 artifact를 새 로직으로 재생성해야 한다.
- 단일 종목이 없는 macro/theme 뉴스는 `종목 미분류`가 아니라 화면에서 `시장/테마 뉴스`로 보여주는 wording 개선이 별도 UI 작업으로 남아 있다.
