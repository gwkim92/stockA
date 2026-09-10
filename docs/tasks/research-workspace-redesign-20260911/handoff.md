# 인계

## 현재 결과

사용자의 레퍼런스 조사 후 진행 요청을 실제 제품 코드에 적용했다. 기업 탭·재무 표·원천 패널, 뉴스 목록과 선택 상세, 홈 우선 검토 목록, 보유 비교 표를 구현했다. 공통 토큰·메뉴도 같은 방향으로 정리했다. 현재 브랜치는 `codex/research-workspace-redesign-v1`이며 과거 v1 task 문서와 이번 20260911 task 문서를 구분한다.

실제 미리보기: http://127.0.0.1:13321 — 운영 자료를 읽는 로컬 production build. 기존 운영 접속 http://127.0.0.1:13309 에는 이번 디자인을 배포하지 않았다. Chrome의 새 리서치 화면 탭(1527793428)과 캡처 갤러리 탭(1527793431)을 남긴다. 캡처 모음은 http://127.0.0.1:13322 이며, 필요하면 `python3 -m http.server 13322 --bind 127.0.0.1 --directory output/playwright/research-workspace-redesign-20260911`로 다시 연다.

## 재실행

프로젝트 루트에서 `python3 docs/tasks/research-workspace-redesign-20260911/readonly_preview.py`로 localhost 18780 GET 프록시를 시작한다. 기존 EC2 SSH 접근과 서버의 기존 read credential이 필요하며 비밀값을 로컬로 복사하지 않는다.

apps/web에서 빌드한 다음 `STOCKANALYSIS_FRONTEND_API_BASE_URL=http://127.0.0.1:18780 STOCKANALYSIS_FRONTEND_API_READ_TOKEN=local-get-only-preview npm run start -- -p 13321`을 실행한다. 표식은 로컬 프록시 연결용이며 운영 인증 토큰이 아니다. 프록시는 GET만 제공한다.

## 검증과 자료

- qa.md: 523개 단위, 160개 브라우저 시나리오, 타입·빌드, 실제 화면과 실패 수정 내역.
- review.md: 자체 검토와 남은 범위.
- design-system.md: 레퍼런스 적용 위치와 토큰·상태 규칙.
- output/playwright/research-workspace-redesign-20260911/: 28개 캡처, JSON, 로그, manifest, 캡처 모음 HTML.
- capture.js, interactions.js, shared-surface.js: Playwright CLI `run-code --filename=...`로 실행하는 캡처·동작 확인.

## 보존 사항

다른 runtime task의 기존 미커밋 변경과 앞선 design-reference-research-20260910 문서를 보존했다. Next dev/build가 만든 임시 AGENTS.md/CLAUDE.md와 next-env.d.ts 변화는 제품 변경에 포함하지 않았다. 추천 weight, benchmark, 평가 표본, schema, 모델·인증 설정, 서버 환경과 실거래 경계는 변경하지 않았다.

운영에 반영하려면 이 브랜치의 UI 변경을 검토한 후 기존 develop 통합·CI·배포 절차로 이어간다. 아직 푸시·운영 배포 증거는 없다.
