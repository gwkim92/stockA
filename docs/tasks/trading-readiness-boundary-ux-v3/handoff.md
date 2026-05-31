# trading-readiness-boundary-ux-v3 Handoff

## Status

- completed: `/trading-readiness` 화면을 실제 주문 차단과 가상 매매 검증 중심으로 정리했고 EC2/Playwright smoke까지 확인했다.

## Completed

- completed: task contract를 생성했다.
- completed: `페이퍼`, `가상 거래`, `주문 경계` 계열의 주요 사용자 노출 문구를 `가상 매매`, `가상 매매 검증`, `실거래 상태`로 정리했다.
- completed: 가상 매매 검증과 실제 주문 제출 기능이 분리되어 보이도록 상단 카드와 세부 섹션 문구를 정리했다.
- completed: EC2 `stockanalysis-web.service`에 배포했고 `/trading-readiness`가 `200`으로 응답한다.

## Boundaries

- broker/order flow, 계좌 권한, 주문 한도, kill switch, paper validation 계산, DB/API DTO는 변경하지 않는다.

## Verification Log

- passed: `cd apps/web && npm run typecheck`
- passed: `cd apps/web && npm run build`
- passed: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task trading-readiness-boundary-ux-v3`
- passed: `git diff --check`
- passed: EC2 deploy and route/content smoke. Required terms `실거래 경계 판정판`, `실거래 차단`, `실제 주문 전송`, `가상 매매 검증`, `실거래 상태`, `킬 스위치` present.
- passed: Playwright snapshot for `http://127.0.0.1:13000/trading-readiness`; required terms present and visible forbidden terms `페이퍼 검증`, `가상 거래`, `주문 경계`, `broker submit`, `read_only_no_order` absent.

## Exact Next Step

- exact next step: 다음 화면 `/performance` 또는 `/remediation`을 같은 방식으로 사용자용 문구와 판단 흐름 기준으로 정리한다.
