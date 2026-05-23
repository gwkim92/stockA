# Review

## Summary

- 전체 주요 화면의 사용자-facing 문구 회귀를 점검했다.
- 공통 추적 메타데이터에서 내부 실행 ID와 `"null"` 문자열이 그대로 노출되지 않도록 정리했다.
- 추천 상세, 투자 논리 상세, 성과 측정, 포트폴리오 커버리지의 어색한 내부 용어를 사용자 판단 언어로 바꿨다.

## Changes

- `AuditMetadata`는 빈 값, `"null"`, 내부 `pipeline-run-*` 문자열을 사용자용 표시로 정규화한다.
- `/recommendations/[recommendationId]`는 “값 없음”, “상세 화면 준비 중” 대신 계산/근거 연결 상태를 설명한다.
- `/theses/[thesisId]`는 “이벤트 원장”과 “준비 중” 표현을 제거했다.
- `/performance`, `/portfolio/coverage`는 “관문” 표현을 “성과 검토 기준”, “커버리지 확인”으로 바꿨다.
- `koLabel`의 template placeholder 번역을 사용자 화면 상태 표현으로 바꿨다.

## Verification

- PASS: `git diff --check`
- PASS: `cd apps/web && npm run typecheck`
- PASS: `cd apps/web && npm run build`
- PASS: `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task full-site-ia-regression-pass`
- PASS: EC2 deploy at `0b9d40d`; FastAPI and web services active.
- PASS: EC2 `/__ready` probe.
- PASS: browser-rendered route text check for 18 representative routes through `http://127.0.0.1:13000`.

## Operational Note

- Cafe public IP `121.167.105.244/32` was added to security group `sg-0a2d52009e73a59e3` for SSH access through AWS Console CloudShell.
- The repo-local `dogfood-output/` directory remains untracked and untouched.
