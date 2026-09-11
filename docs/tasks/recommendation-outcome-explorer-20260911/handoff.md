# Handoff — 진행 중

현재 branch `codex/recommendation-outcome-explorer-v1`, base `cfa384282feae8e0dcb52246f136c752b583c17a`.

- `/performance/recommendations` 및 `/api/recommendation-outcomes` 구현. 사이드바 판단 성과와 기업/보유 성과 링크 연결. 기존 `/performance` 보유 귀속/평가 이력 유지.
- 구현/검증 범위는 contract, plan, qa, review 참고. 운영 자료 읽기 1233건 확인. 새 AI 호출/DB write 없음.
- 다음: 최종 브라우저 QA → 검증된 feature PR/develop 통합 → Linux artifact와 동일 코드 활성화 → 운영 API/Chrome 확인.
- `readonly_preview.py`: local18789 GET-only proxy. 새 read module은 메모리에서 실행하고 나머지는 기존 authenticated GET에 연결. 운영 파일/DB 수정 없음. preview Web13329.
- `activate_runtime.py`: 이번 작업 전용 receipt path와 검증된 Linux artifact를 사용한다. 기존 배포 receipt/repair 작업은 재실행하지 않는다.
- 다른 task의 기존 dirty/untracked 문서는 이번 커밋 범위에서 제외한다.
