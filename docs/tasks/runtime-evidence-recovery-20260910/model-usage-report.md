# stockA 인증 경로와 모델 — 2026-09-10

현재 EC2의 로그인 인증 경로에서 실제로 선택된 모델은 **GPT-5.5 (`gpt-5.5`)**다. `codex_oauth`는 인증/호출 방식이고, DB에 저장되는 `codex-cli-default`는 모델 이름이 아니라 CLI 기본값을 사용한다는 표시다.

## 실제 실행 근거

- 대상: 개인 계정 stockA EC2, `/opt/stockanalysis/app`, 코드 `25d1ace3` 및 후속 인계 문서 커밋.
- Codex CLI: `/usr/bin/codex`, `codex-cli 0.132.0`.
- 사용자 승인 후 `/opt/stockanalysis/runtime/data-operations.env`의 `STOCKANALYSIS_LLM_PROVIDER`를 `agents_sdk_openai`에서 `codex_oauth`로 변경했다. 기존 파일은 서버 내부에 백업했다. 시크릿·주기·처리 건수는 변경하지 않았다.
- provider를 명령행에서 강제하지 않은 실제 뉴스 번역 실행 `23560`이 설정을 읽어 `provider=codex_oauth`, 갱신 1건, 실패 0건으로 완료됐다.
- 해당 실행의 Codex CLI 출력 헤더: `model=gpt-5.5`, `provider=openai`, `reasoning effort=none`, `reasoning summaries=none`.
- 실제 실행 인자에 `--model`은 없고 `--ignore-user-config`가 있다. 따라서 GPT-5.5를 프로젝트가 명시적으로 고정한 상태는 아니다. CLI/계정 기본값이 바뀌면 이후 실행 모델도 달라질 수 있다.
- 원문 실행 로그는 서버 안에만 두고 모델 헤더만 로컬 `artifacts/runtime-evidence-recovery-20260910/configured-provider-model-audit.json`에 추출했다.

## 작업별 경로

| 작업 | 인증/호출 방식 | 모델 선택 | 검증 범위 |
| --- | --- | --- | --- |
| 뉴스 한국어 번역 | 로그인 인증 `codex_oauth` | Codex CLI 기본값, 이번 실제 실행은 GPT-5.5 | 실제 모델 헤더와 DB 갱신 확인 |
| 뉴스 구조화·근거 추출 | 로그인 인증 `codex_oauth` | 같은 CLI 기본값 | 실제 성공 `23558` 및 전환 후 배치 `23569`의 10/10개 성공. 이 작업의 모델 헤더는 따로 채집하지 않음 |
| 사이클 흐름 요약 | 로그인 인증 `codex_oauth` | 같은 CLI 기본값 | 실제 성공 `23559`, `llm_used=true`; 모델 헤더는 따로 채집하지 않음 |
| 기업 리서치 보고서 | 로그인 인증 `codex_oauth` | 같은 CLI 기본값 | 코드와 일일 실행 명령 확인. 이번 세션에서 신규 실제 실행하지 않음 |
| 기존 뉴스 API 경로 | API 키 `agents_sdk_openai` | `gpt-5.5` 명시 | registry와 최근 실패 invocation으로 확인. 자동 뉴스는 이 경로에서 전환함 |
| 뉴스 군집 요약 등 규칙 처리 | 인증 없음 `local_rules` | `news_cluster_summary_v1` 등 규칙 이름 | LLM 모델이 아님 |
| 뉴스 품질 회귀평가 | 인증 없음 `fixture` | `news-ai-eval-fixture-v1` | 고정 정답 세트 검증이며 실제 LLM 호출이 아님 |

인증 모델 근거를 찾은 운영 코드 범위에는 별도의 Claude/Gemini 로그인 호출 경로가 없다. 위 모델명은 서버 애플리케이션의 실행 모델이며, 현재 대화 중인 Codex 앱 에이전트의 모델을 뜻하지 않는다.

전환 후 기존 systemd `news-intraday` 한 주기도 2026-09-10 07:03 UTC에 완료됐다. 10개 단계 모두 성공했고, 실제 Codex 번역 20건과 구조화 10건의 호출·DB 저장·근거 검증이 모두 통과했다. 다음 timer는 기존 설정대로 08:00 UTC(17:00 KST)이며, 그 예약 실행은 아직 관찰하지 않았다.

## 추론 강도 기록의 불일치

뉴스·사이클·기업 리서치 runner의 기본 `reasoning_effort`는 `low`이고 DB도 이를 저장한다. 그러나 Codex subprocess 명령에는 `model_reasoning_effort`를 설정하는 인자가 없으며 이번 번역 실제 헤더는 `none`이었다. 따라서 **저장된 `low`를 실제 적용값으로 보고하면 안 된다.** 이는 모델 성능 비교와 평가 재현성에 영향을 주는 관측 문제다. 이번 요청은 제공자 전환과 사용 모델 확인이므로 추론 강도나 모델을 임의로 변경하지 않았다.

## 코드와 문서

- `src/stockanalysis/ingest/news/translation.py`: Codex 실행 인자, 명시 모델 조건.
- `src/stockanalysis/ingest/news/ai_extract.py`, `src/stockanalysis/ai/cycle_community_ai_summary.py`, `src/stockanalysis/ai/equity_research_reporting.py`: 같은 CLI 기본 모델 선택 방식.
- `src/stockanalysis/ai_agents/registry.py`: API 기본 모델 `gpt-5.5`, Codex 대체 경로 `codex-cli-default`.
- `src/stockanalysis/ai_agents/runtime_policy.py`: provider별 모델 이름 선택.
- [OpenAI 공식 구성 문서](https://learn.chatgpt.com/ko-KR/docs/config-file/config-basic): CLI 플래그, 설정 파일 및 기본값의 우선순위. 이 문서만으로 현재 EC2의 실제 모델을 추정하지 않고 위 실행 헤더로 확인했다.
