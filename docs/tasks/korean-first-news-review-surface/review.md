# Task Review

## Result

- `NewsTitleBlock`을 한국어 우선 표시로 바꿨다.
- 영어 뉴스 제목은 기본 본문에서 빼고 `영어 원문 제목 보기`로 접었다.
- 원천 문서 상세에 `한국어 검토 요약` 패널을 추가했다.
- 원천 문서의 발췌와 연결 AI 근거도 한국어 요약을 먼저 보여준다.
- AI 근거 상세의 모델 입력 근거와 종목 상세의 원문 근거 미리보기도 `한국어 요약: ... 관련 원천 근거` 형태로 바꿨다.

## Verification

- 실행한 검증:
  - `git diff --check`
  - `cd apps/web && npm run typecheck`
  - `cd apps/web && npm run build`
  - `PYTHONPATH=/Users/woody/ai/agent-work-harness/src python3 -m awh verify --repo . --task korean-first-news-review-surface`
  - EC2 deploy 후 `npm --prefix apps/web run build`
  - EC2 service status: `stockanalysis-web.service` active, `stockanalysis-frontend-api.service` active
  - Playwright render check for `http://127.0.0.1:13000/ai-evidence/ai-evidence-251`
  - Playwright render check for `/source-documents/rss%3Amarketwatch-topstories%3Ab057be957d391c978876835f`

## Evidence

- EC2 deployed commit: `6a05c97`
- Playwright screenshots:
  - `/private/tmp/stockanalysis-runtime/korean-first-ai-evidence-251-final.png`
  - `/private/tmp/stockanalysis-runtime/korean-first-source-document-final.png`
- Render check result: Korean-first labels present, raw English news title absent from default AI evidence text, production error text absent.

## Remaining Risks

- 이번 변경은 화면 계층에서 한국어 검토 요약을 먼저 보여주는 것이다. 원문 전체의 문장 단위 번역을 DB에 저장하는 것은 아직 구현하지 않았다.
- 정확한 한국어 제목/요약 품질을 높이려면 Codex OAuth batch에서 `korean_title`, `korean_summary`, `translation_confidence`를 생성하고 validator를 거쳐 저장해야 한다.
