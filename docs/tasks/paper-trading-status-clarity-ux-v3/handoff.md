# paper-trading-status-clarity-ux-v3 Handoff

## Status

- completed: `/paper-trading` 화면의 가상 매매 상태, 실거래 차단, 후보 검토 문구를 정리하고 EC2 반영·route smoke·Playwright snapshot 검증까지 완료했다.

## Completed

- completed: task contract를 생성했다.
- completed: 화면 제목과 판정판을 `가상 매매 검증` 기준으로 정리했다.
- completed: 실제 주문 전송 0건, 가상 매매 후보, 차단 조건, 위험 예산 연결, 후보 목록을 한 흐름으로 읽히게 문구를 정리했다.
- completed: `페이퍼`, `주문 경계`, `eval_run_id`, `active share`, `broker flow`, `paper validation` 같은 내부 표현이 주요 화면 문구로 노출되지 않게 했다.
- completed: 차단 사유 설명도 화면 표시 직전에 사용자용 한국어로 치환한다.
- completed: 가상 매매 후보 계산, 추천 산식, DB/API, scheduler, AI batch, broker/order flow는 변경하지 않았다.

## Boundaries

- recommendation weight, scoring formula, benchmark, portfolio position, broker/order flow는 변경하지 않는다.
- API, DB schema, scheduler, AI batch는 변경하지 않는다.

## Verification Log

- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task paper-trading-status-clarity-ux-v3`
- passed: `git diff --check`
- passed: commits `4309ed15`, `c43e6859` pushed to `origin/codex/local-mvp-runtime-aws-bootstrap`.
- passed: EC2 `git pull --ff-only`, Next typecheck/build, and `stockanalysis-web.service` restart returned `active`.
- passed: EC2 route/content smoke for `/paper-trading` returned 200 and required terms were present: `현재는 실거래가 아니라 가상 매매 검증 단계`, `가상 매매 판정판`, `실제 주문 전송 0건`, `가상 매매 검증`, `실거래 상태`, `위험 예산 연결`, `시뮬레이션 후보 목록`, `실거래 안전장치`.
- passed: EC2 content smoke found no targeted visible forbidden terms: `페이퍼`, `주문 경계`, `eval_run_id`, `active share`, `broker flow`, `paper validation`.
- passed: Playwright snapshot for `http://127.0.0.1:13000/paper-trading` confirmed the same required terms and no targeted forbidden terms.

## Exact Next Step

- exact next step: continue page-by-page UX refactor with `/portfolio/coverage`, because 추천·가상 매매 화면에서 다음으로 이동하는 보유 검토/위험 예산 화면의 용어와 구조가 아직 같은 수준으로 정리되지 않았다.
