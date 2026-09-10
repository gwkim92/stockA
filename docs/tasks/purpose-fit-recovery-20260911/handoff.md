# 운영 반영·성과 복구 완료, 실제 기업 AI 호출 승인 대기

2026-09-11 KST. PR #52 구현·CI·develop 통합 후, 사용자가 서비스 재시작을 포함한 운영 배포, 성과 1,009건 복구, NVDA/AAPL/ARM 실제 AI 리서치 3건 생성을 “진행”으로 승인했다. 배포와 성과 복구는 완료했다. 실제 리서치 호출은 아래 별도 자동 승인 검토 거절로 실행하지 못했다.

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

## 아직 해결되지 않은 점

1. **실제 기업 리서치 3건은 미실행이다.** 자동 승인 검토가 내부 재무·뉴스·추천/thesis 자료를 OpenAI Codex OAuth로 전송하고 운영 DB에 저장하는 데 대한 payload/목적지별 승인이 부족하다는 이유로 명령 실행 전 거절했다. 전송 예정 자료를 서버 내부에서 읽기 전용 검사한 뒤 같은 명령을 근거와 함께 재검토 요청했으나 다시 거절됐다. 다른 경로로 우회하지 않았다.
2. 선택 입력은 NVDA 15,854자, AAPL 15,941자, ARM 14,213자. 계좌/보유 테이블은 조회하지 않는다. private key/API key/AWS key/Bearer/DB주소 패턴은 검출되지 않았다. 공개 재무·뉴스뿐 아니라 앱 생성 추천·투자 논리도 포함한다. `research-payload-preflight.json`에 필드·목적지·prompt hash를 기록했다. 단순 패턴 검사가 모든 민감정보의 부재를 보증하는 것은 아니다.
3. 사용자에게 해당 자료를 기존 OpenAI Codex OAuth의 gpt-5.6-terra로 전송해 3건을 만들고 운영 DB에 저장할지 명시한 확인을 요청했다. 답변이 필요하다. 승인 전까지 research 단계를 실행하지 않는다. 화면의 기존 대체 보고서는 실제 AI 성공 결과가 아니다.
4. `/performance`의 2026-09-10/09-04 조회는 0행이다. 이 화면은 해당 종료일의 `performance.attribution_run`과 보유 스냅샷에 연결된 결과만 보여준다. 전체 추천 outcome backfill은 별도 귀속 보고서를 생성하지 않는다. 이를 투자 성과 0이나 추천 복구 실패로 해석하지 않는다. 귀속 보고서와 전체 추천 성과 탐색은 후속 과제다.
5. `/api/data-health`는 여전히 `attention_required`, open gates 8개: alert_destination, data_operations_artifact_runner, live_ai_invocation_health_attention, benchmark_drift_quality_attention, portfolio_review_decision_history_attention, portfolio_review_decision_feedback_attention, portfolio_review_feedback_calibration_attention, portfolio_review_feedback_cadence_attention. 이번 작업은 이 항목을 임의 해제하지 않았다.

## 이어서 실행할 단계

승인이 도착하면 현재 날짜·모델 설정·운영 commit과 기존 receipt/DB 이력을 먼저 확인한다. 아래 경로의 연구 phase는 시작 파일을 배치별로 남기므로 중단 후 무조건 반복하지 않는다. 이미 완료한 preflight/outcomes/activation은 재실행하지 않는다.

`PYTHONPATH=/opt/stockanalysis/app/src /opt/stockanalysis/venv/bin/python /opt/stockanalysis/runtime/purpose-fit-recovery-20260911/recover_runtime.py research`

실제 생성은 NVDA/AAPL/ARM 각 1건이며 기존 Terra 설정을 사용한다. primary 성공·실제 CLI 선택 모델·DB 저장·fallback 0건과 기존 행 보존을 확인한다. 내용의 기업별 근거, 자료 누락, 관측 가능한 다음 조건을 검토하고 운영 API/Chrome 캡처를 갱신한다. 이전 결과 또는 fallback을 성공 증거로 사용하지 않는다.

네트워크 전송·운영 명령에는 독립 SSH 연결을 사용한다. 사용자 13309 터널과 대용량 전송을 공유하지 않는다. 기존 사용자 문서 변경은 보존했다. 임시 PostgreSQL 55487은 종료 상태다. 13321/18779는 이전 로컬 미리보기이며 운영 검증 증거로 쓰지 않았다.
