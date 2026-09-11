# 운영 반영·성과 복구·기업 AI 표본 생성 완료

2026-09-11 KST. PR #52 구현·CI·develop 통합과 운영 배포, 성과 1,009건 복구에 이어 NVDA/AAPL/ARM 실제 AI 리서치 3건을 생성·저장하고 운영 화면을 검증했다. 자동 승인 검토의 외부 전송 보류는 재무·뉴스·앱 생성 추천·투자 논리, OpenAI Codex OAuth/Terra 목적지, 생성 3건 및 운영 DB 저장을 명시한 질문에 사용자가 다시 “진행”으로 승인한 뒤 해소됐다.

## 배포 증거

- 개인 AWS `115623963546`, 인스턴스 `i-029d51b163fb07b61`, us-east-1을 IMDS로 재확인했다.
- EC2 develop: `359e8531` → `57b6bba9bf0f66605220472f27d117e1134bd8b4`.
- 검증된 Linux artifact: `c0e892a3f9ca28f14cb320dd7f8fac552551bcaf`, BUILD_ID `PGVFE-6JtVuU6b53yBvzj`, SHA-256 `f88c276adafca5392cb9e6810ea3959895172189dd6e531a5e92436ca4483a6c`.
- API ready=ok, 웹 3000/13000 주요 경로 200, 세 서비스 active, 타이머 13개 복원.
- 모델 `gpt-5.6-terra`, revision 2, overrides 없음. 환경 파일 내용 hash·파일 권한과 모델 설정이 배포 전후 동일하다. DB migration 없음.
- 원본과 이전 Next build는 `/opt/stockanalysis/runtime/purpose-fit-recovery-20260911/`에 보관했다. `activation.json`이 존재하므로 활성화 스크립트를 재실행하지 않는다.

## 성과 복구 증거

기준일은 2026-09-10이다. 승인 대기 중 DB가 갱신되어 실행 직전 추천 1,358개, 추천 성과 224개, thesis 성과 126개였다. 기존 모든 행의 지문을 기준으로 보존 검사를 수행했다. 최초 조사 때의 119개와 현재 224개는 다른 시점의 수치다.

| 묶음 | parent run | 추천 성과 추가 |
|---|---|---:|
| 1 | 23731 | 237 |
| 2 | 23752 | 322 |
| 3 | 23773 | 340 |
| 4 | 23794 | 110 |
| 합계 | 66 batch×horizon | 1,009 |

- 실패 후보 0개. 추천 성과 총 1,233개, thesis 성과 746개.
- 기존 추천 1,358개, 점수 구성요소 32,593개, 포지션 515개, 벤치마크 612개와 기존 추천/thesis 성과 행 hash 모두 보존.
- calibration run 23801 / eval 1756, router run 23804 / eval 1757.
- 감사 대상 5,432개 추천×기간 중 기간 조건에 맞는 측정 1,128개, 미도래 4,304개, 준비된 미처리 0개, 가격 누락 0개. 총 저장 행 1,233개와 감사 기간에 맞는 1,128개를 혼동하지 않는다.
- 30일 창 920개, 90일 창 208개, 180/365일 창은 아직 0개. 기존 ±7일 관측 기준을 유지했다.
- 다음 측정일 2026-09-11, 대상 21개. 기존 router가 판단하며 이번에 추가 실행하지 않았다.
- 추천 weight, benchmark 정의, 포지션, 주문 경계는 변경하지 않았다. 표본 평가가 `ready_for_weight_review`여도 별도 승인 없는 weight pilot은 시작하지 않는다.

## 실제 API·Chrome 검증

- 사용자 터널 `http://127.0.0.1:13309` 정상. 로컬 preview가 아닌 운영 서버를 검사했다.
- NVDA recommendation-1497, ARM recommendation-1490의 목록/상세 `decision_boundary`가 완전히 동일하다. 가상 검증 입력 가능, 성과 미측정, 주문 불가.
- 과거 AAPL recommendation-477: 2026-07-24 종료 성과 저장, `outcome_measured=true`, `decision_review_ready`. 이 상태는 투자 판단 승인이나 수익성 입증이 아니다.
- 기업·추천 상세·성과·data-health의 1440×1000 / 390×844 총 8개 화면: HTTP 200, 가로 넘침 없음, pageerror 없음.
- NVDA 입력 문서 1 → source-document-40343 패널에 공개일·수집일·발췌 표시. 모바일 패널, Escape 닫기, 버튼으로 포커스 복귀 통과.
- AI 운영 화면에 Codex 작업 5개, 기본 Terra, CLI 선택 모델과 DB 이력, 관리자 잠금 해제 및 변경 UI가 표시된다. 현재 검증 세션은 조회 전용이며 모델 변경 저장은 이번 작업에서 실행하지 않았다.
- 캡처: `output/playwright/purpose-fit-production-*.png`. API·실행 원본 및 검사 결과: `output/purpose-fit-recovery-20260911/`, `output/purpose-fit-20260911/recovered-*.json`.

## 실제 기업 AI 생성 결과

기준일 2026-09-10을 유지했다. 2026-09-11 00:15~00:16 UTC 실제 호출이며 운영 정책은 기존 gpt-5.6-terra / revision 2다. 호출·소스 변경 없이 준비된 `recover_runtime.py research`를 한 번 실행했다.

| 기업 | pipeline run | invocation | artifact | 입력 문서 |
|---|---:|---:|---:|---:|
| NVDA | 23818 | 41113 | 492 | 6 |
| AAPL | 23819 | 41114 | 493 | 4 |
| ARM | 23820 | 41115 | 494 | 2 |

- primary 3건, failed 0건, fallback 0건. 실제 결과 receipt와 DB/API model_name 모두 gpt-5.6-terra다. 요청 이름 `codex-cli-default`와 구분했다.
- 세 기업 API의 generation.mode=ai, structural_status=complete, content_review_status=not_recorded. NVDA 추천 상세도 artifact 492를 반환한다.
- 모델 설정 화면은 기업 리서치 최근 성공 Terra, invocation 41115를 표시한다. 기본 모델과 overrides는 변경하지 않았다.
- research-verified.json에서 기존 추천·점수·포지션·벤치마크 및 기존 성과 행 보존 검사가 통과했다. 총 추천 성과 1,233개, thesis 성과 746개 유지.
- Chrome 세 기업 × desktop/mobile 6개 화면: HTTP 200, 실제 AI·Terra 모델 표시, 가로 넘침 없음, pageerror 없음. 연결된 문서 12개는 모두 200/발췌 1개 이상. 새 ARM 원천 패널에서 2026-08-24 문서와 발췌, 모바일, 닫기를 확인했다.
- 캡처 `output/playwright/purpose-fit-ai-{nvda,aapl,arm}-{desktop,mobile}.png`, ARM 원천 캡처, AI 설정 캡처. API 결과와 receipt/검증 JSON은 `output/purpose-fit-recovery-20260911/`와 `output/purpose-fit-20260911/research-*.json`에 보관했다.

## 내용 검토와 남은 과제

1. **생성 성공은 투자 판단의 정확성 검증이 아니다.** 3건 모두 원천 부족, 입력에서 제외한 범주, 현재 thesis가 불변 역사 기록이 아니라는 한계를 밝힌다. NVDA는 확인된 사업 촉매를 임의로 채우지 않아 0개이며, AAPL/ARM은 보도된 제품·사업 변화와 후속 확인 조건을 연결한다. 화면의 내용 검토 미기록을 임의 변경하지 않았다. 상세 표본 검토는 research-review.md를 따른다.
2. **AAPL 원천 연결 불일치**: event-19/source-document-22의 영문 제목은 AeroVironment 드론 기사이나 한국어 번역은 다른 시장 뉴스이며 AAPL supportive 연결이 남아 있다. 읽기 전용 컨텍스트 재조회로 확인했다. 이번 AAPL 보고서는 해당 이벤트를 핵심 주장·촉매로 인용하지 않았지만 입력 문서 목록에는 포함된다. 원천 갱신 후 번역·이벤트·종목 연결의 일관성을 복구하는 후속 작업이 필요하다. 이 행을 삭제·재분류하거나 추가 AI 호출을 실행하지 않았다.
3. 원천 재무 누락, 경제/테마 분류를 이용한 피어 비교군의 기업 적합성, RSS 제목 중심 근거, 데이터 시점과 현재 가격의 차이가 남는다. 이를 모델 생성만으로 해소했다고 보고하지 않는다.
4. `/performance`의 2026-09-10/09-04 조회는 0행이다. 해당 종료일의 `performance.attribution_run`과 보유 스냅샷에 연결된 결과를 요구한다. 전체 추천 outcome backfill은 별도 귀속 보고서를 생성하지 않는다. 귀속 보고서와 전체 추천 성과 탐색은 후속 과제다.
5. 00:14 UTC 이전 확인한 `/api/data-health`에는 open gates 8개가 있었다. 마지막 전체 gate snapshot은 이전 운영 검증 결과이며 이번 AI 성공으로 전체 gate 해소를 주장하지 않는다. 알림·보유 검토·귀속 보고서 등의 완료 여부는 별도로 확인해야 한다.

## 인계와 재실행 방지

`activation.json`, `outcomes-verified.json`, `research-{NVDA,AAPL,ARM}.json`, `research-verified.json`이 존재한다. 완료한 activate/preflight/outcomes/research 단계를 다시 실행하지 않는다. 원격 검증 폴더는 `/opt/stockanalysis/runtime/purpose-fit-recovery-20260911/`다. 추가 기업이나 날짜의 AI 호출은 이번 3건에 포함하지 않는다.

다음 우선순위는 원천 문서·번역·이벤트 연결 일관성, 재무 원천/피어 비교군의 적합성, 포트폴리오 귀속 보고서와 전체 추천 성과 탐색이다. 추천 weight·평가 기준·실거래 경계는 그대로 유지한다.

네트워크 전송·운영 명령에는 독립 SSH 연결을 사용한다. 사용자 13309 터널과 대용량 전송을 공유하지 않는다. 기존 사용자 문서 변경은 보존했다. 임시 PostgreSQL 55487은 종료 상태다. 13321/18779는 이전 로컬 미리보기이며 이번 운영 검증 증거로 쓰지 않았다.
