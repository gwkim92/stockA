# 기능·화면 평가 QA

평가일 2026-09-10. 개인 EC2 운영 웹을 SSH 터널 `http://127.0.0.1:13309`로 읽었다. 배포 `f9f1d5ee`, 로컬 검토 `80769207`. 독립 평가 브라우저 `stocka-evaluation`을 사용했다. 사용자 Chrome의 인증·모델 설정은 조작하지 않았다.

## 주요 화면

각 화면의 첫 렌더·주요 텍스트·링크/입력 목록·문서 폭과 높이·브라우저 오류를 기록했다. 주요 20개 모두 요청한 화면을 렌더링했다. 이것은 모든 하위 영역과 기능의 통과라는 뜻이 아니다. 데스크톱 1440×1000, 모바일 390×844. 독립 시각 검토자는 이 40개 첫 화면을 직접 검토했다.

| 경로 | 데스크톱 문서 폭 | 모바일 문서 폭 | 관찰 |
|---|---:|---:|---|
| `/` | 1440 | 390 | 요청 화면 렌더 확인 |
| `/market-map` | 1440 | 390 | 요청 화면 렌더 확인 |
| `/cycle-map` | 1440 | 390 | 요청 화면 렌더 확인 |
| `/intelligence` | 1440 | 390 | 요청 화면 렌더 확인 |
| `/stocks` | 1440 | 390 | 요청 화면 렌더 확인 |
| `/recommendations` | 1440 | 390 | 요청 화면 렌더 확인 |
| `/portfolio/coverage` | 1440 | 390 | 요청 화면 렌더 확인 |
| `/performance` | 1440 | 390 | 요청 화면 렌더 확인 |
| `/paper-trading` | 1440 | 390 | 요청 화면 렌더 확인 |
| `/research-notes` | 1440 | 390 | 요청 화면 렌더 확인 |
| `/cycles` | 1440 | 390 | 요청 화면 렌더 확인 |
| `/events` | 1440 | 390 | 요청 화면 렌더 확인 |
| `/ai-evidence` | 1440 | 390 | 요청 화면 렌더 확인 |
| `/ai-evidence/results` | 1440 | 390 | 요청 화면 렌더 확인 |
| `/ai-evidence/blocked` | 1440 | 390 | 요청 화면 렌더 확인 |
| `/events/classification` | 1440 | 390 | 요청 화면 렌더 확인 |
| `/data-health` | 1440 | 406 | 모바일 가로 넘침, ISSUE-007 |
| `/admin/ai-agents` | 1440 | 390 | 요청 화면 렌더 확인 |
| `/trading-readiness` | 1440 | 390 | 요청 화면 렌더 확인 |
| `/remediation` | 1440 | 390 | 요청 화면 렌더 확인 |

증거: `desktop-coverage.jsonl`, `mobile-coverage.jsonl`, `screenshots/*-desktop.png`, `*-mobile.png`, `snapshots/*.json`, `*.txt`. 전부 `artifacts/product-evaluation-20260910/` 아래다. 첫 화면 밖 전체가 시각 검사를 통과했다는 뜻은 아니다. 브라우저 오류 출력이 비어 있어도 데이터 의미·링크·서버 오류가 없음을 보장하지 않는다.

## 대표 상세

| 경로 | 확인 결과 |
|---|---|
| `/stocks/NVDA` | 대표 자료 렌더 확인 |
| `/recommendations/recommendation-1466` | 대표 자료 렌더 확인 |
| `/themes/AI_SEMICONDUCTOR_CYCLE` | 대표 자료 렌더 확인 |
| `/theses/thesis-6` | 대표 자료 렌더 확인 |
| `/ai-evidence/ai-evidence-3680` | 대표 자료 렌더 확인 |
| `/ai-evidence/ai-evidence-3665` | 대표 자료 렌더 확인 |
| `/source-documents/source-document-rss%3Ayahoo-finance-news%3Abc514fa20dd706c5cdd354a6` | 원천 링크 목적지 404, ISSUE-006 |
| `/portfolio/coverage/details` | 대표 자료 렌더 확인 |
| `/performance/evaluations` | 대표 자료 렌더 확인 |
| `/stocks/NVDA/review` | 대표 자료 렌더 확인 |
| `/stocks/NVDA/details` | 대표 자료 렌더 확인 |
| `/performance/evaluations/1720` | 대표 자료 렌더 확인 |

`/stocks/NVDA/review`, `/stocks/NVDA/details`, `/performance/evaluations/1720`은 모바일도 추가 캡처했다. 세 화면 문서 폭은 모두 390px다. 대표 RSS 원천의 접두사 없는 주소도 실제 클릭 후 404를 확인했다. 따라서 상세 12개 경로 중 11개는 대상 내용을 읽었고 1개는 오류였다. 같은 원천의 별칭 경로를 정상 상세 한 건으로 더하지 않는다.

## 실제 동작 및 상태

| 흐름 | 결과 | 증거/범위 |
|---|---|---|
| 종목 탐색 → NVDA 검색 → 직접 상세 대조 | 실패 | 검색은 첫 50개 밖 NVDA를 찾지 못한다. `issue-002-step-1/2/3.png`, `issue-002-stock-search.webm` |
| 분석 근거 CNM → 원천 문서 | 실패 | 목록 버튼 실제 클릭 후 404. `issue-006-list-before/after.png`, `issue-006-list-after.json`, `issue-006-source-link-confirmed.webm` |
| 같은 CNM AI 상세 → 원천 문서 | 실패 | 접두사 없는 RSS 주소도 404. `issue-006-source-canonical.json`, `issue-006-step-3.png` |
| NVDA 검토 노트 작성 → 저장 → 새로고침 | 통과 | `review-save-final.txt`, `review-restored-confirmed.txt`; 내용 복원 확인 |
| 내 검토함 → 저장한 NVDA 메모 선택 | 통과 | `notes-with-test-record-confirmed.txt`, `notes-selected.txt`; 저장 당시 메모와 현재 분석 이동을 구분 |
| 메모 수정 → 저장 → 재접속 | 통과 | `review-edited-confirmed.json`; '수정 확인 완료' 복원 |
| 테스트 메모 삭제 → 확인 → 검토함 | 통과 | 인라인 `삭제 확인` 후 `notes-deletion-confirmed.txt`; 빈 검토함 확인. 다른 사용자의 메모에 접근하지 않음 |
| 모바일 전체 메뉴 열기/닫기 버튼 | 통과 | `mobile-menu-open.txt`, `mobile-menu-close-confirmed.json` |
| 모바일 빠른 이동에서 NVDA 입력 → 상세 | 통과 | `mobile-quick-search.txt`, `mobile-quick-nav-result.json`. 데이터 존재 여부는 상세에서 확인하는 직접 이동임을 UI가 설명 |
| 홈 재검토/AI 이력/뉴스 지표/성과 게이트 | 결함 확인 | ISSUE-001·003·004·005: 화면 DOM과 독립 코드 검토를 대조 |
| 전문 분석 시점 혼합 | 결함 확인 | NVDA의 2012년 현금흐름 지표와 2026년 모델/추정 입력. 운영 DB 행 계보는 미조회 |
| 기본 성과일 2026-09-10 | 빈 상태 확인 | 0개 결과·시작일 미확인; 0% 수익률로 바꾸지는 않지만 커버리지 게이트 통과가 잘못됨 |
| AI 모델 설정 조회 | 조회 상태 확인 | 작업별 기본/적용/최근 성공 모델/과거 호출 구분. 이번 평가에서 저장·실제 AI 호출은 하지 않음 |
| 거래 안전/페이퍼 화면 | 조회 상태 확인 | 주문 차단/검증 대기 화면을 확인. 실제 주문·거래소 호출·실행 차단 공격 시험은 안 함 |

오류 페이지의 홈·후보 복귀 링크 존재는 확인했으나, 모든 404/timeout/API 부분 실패를 주입한 검사는 아니다. 날짜 조회·모든 필터·평가 기록의 모든 페이지·원천 외부 사이트·내보내기·다른 기기 동기화는 전수 확인하지 않았다.

## 테스트·운영 증거

- 독립 구현 검토자가 관련 frontend 8개 파일 **187개 테스트**, 프로젝트 `.venv`의 Python **25개 테스트** 통과를 확인했다. 대상과 환경은 `implementation-review.md`의 실행한 검증에 기록했다.
- 기본 Homebrew Python에서 FastAPI가 없어 발생한 import 오류는 프로젝트 환경으로 바꾸어 통과했다. 제품 결함으로 집계하지 않았다.
- 운영 readback `runtime-health.txt`: API·웹·공개 웹 서비스 3개 active, 타이머 13개 active. 당시 RAM 1913MiB 중 약 940MiB available, swap 0. 새 배치가 성공했다는 증거는 아니다.
- 뉴스 DOMContentLoaded 18.8/17.1초, 데이터 상태 15.3/15.2초(데스크톱/모바일). `snapshots/intelligence-*.json`, `health-*.json`의 Navigation Timing이다. 캡처 스크립트의 `seconds`는 도구 실행 시간을 포함하므로 페이지 로딩 시간으로 사용하지 않았다.
- 전체 테스트 재실행·새 production build·배포·AI job·DB write·실거래를 하지 않았다. 선택 검사의 통과를 전 시스템 품질 통과로 일반화하지 않는다.

## 도구 오류와 재현 신뢰성

접근성 ref와 스크롤 애니메이션 때문에 초기 저장/클릭이 실제 대상을 누르지 못한 경우가 있었다. 실제 DOM 선택자, 화면 노출, 이동 완료, 저장 메시지와 복원 값을 확인한 결과만 위 표에 사용했다. `review-saved.txt`, `review-reloaded.txt`, `notes-with-test-record.txt`, `review-edited-restored.json`, 초기 `issue-006-source-click.json` 등은 실패한 도구 시도의 중간 기록이며 최종 성공/결함 증거로 사용하지 않는다. `*-confirmed` 및 최종 파일명이 명시된 항목이 우선이다.

모바일 Escape 시도 중 브라우저 도구가 빈 탭 상태가 되어 버튼을 사용해 재검증했다. Escape 키와 포커스 복귀는 제품 통과/실패로 판정하지 않는다. malformed selector 대기 오류도 도구 문제로 분리했다.

## 미확인 영역

모든 자료의 정확성/최신성, 외부 공시 대사, 전체 계산/백테스트, 동시 사용자·부하·장시간 운영, 보안 침투, 모든 권한 저장 흐름, 스크린리더·확대·모션·전체 키보드 접근성, 서로 다른 브라우저/실물 휴대폰은 미검증이다. 모바일은 390px 브라우저 뷰포트 평가다.
