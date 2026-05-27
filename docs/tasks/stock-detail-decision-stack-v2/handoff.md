# stock-detail-decision-stack-v2 Handoff

## Status

- completed: 종목 상세 상단의 판단 순서와 다음 클릭 위치를 정리하는 작업을 완료했다.

## Completed

- completed: task contract를 생성했다.
- completed: `/stocks/[symbol]` hero 직후 `현재 결론` 패널을 추가했다.
- completed: 추천, 보유, 뉴스·상위 흐름, thesis, 페이퍼·주문 상태를 분리한 카드와 CTA를 추가했다.
- completed: 가격, 추천/보유, 상위 흐름, 직접 뉴스 섹션의 읽는 순서와 제목을 명확히 바꿨다.
- completed: 모바일에서 결론 패널과 카드가 한 열로 내려가도록 CSS를 추가했다.

## Boundaries

- recommendation weight, scoring formula, benchmark, portfolio position, broker/order flow는 변경하지 않는다.
- API, DB schema, scheduler, AI batch는 변경하지 않는다.

## Verification Log

- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task stock-detail-decision-stack-v2`
- passed: `git diff --check`
- passed: EC2 deploy `npm run typecheck`, `npm run build`, `sudo systemctl restart stockanalysis-web.service`, `systemctl is-active stockanalysis-web.service`
- passed: local tunnel `/stocks/SPY` route smoke at `http://127.0.0.1:13000/stocks/SPY` confirmed `현재 결론`, `추천`, `보유`, `뉴스·흐름`, `투자 논리`, `페이퍼·주문`, `주문 차단`, `가격 흐름은 추천 근거가 아니라 상태 확인부터 한다`, `회사명이 없어도 거시·테마 흐름은 종목에 영향을 줄 수 있다`
- passed: EC2 internal `/stocks/SPY` route smoke at `http://127.0.0.1:3000/stocks/SPY` confirmed the same strings

## Next Step

- exact next step: 다음 UX slice는 `recommendation-detail-decision-waterfall-v3`로, 추천 상세에서 거시→테마→기업→재무→밸류에이션→리스크→페이퍼 검증 순서를 더 선명하게 만든다.
