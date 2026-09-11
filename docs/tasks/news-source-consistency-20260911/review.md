# 코드 검토

확인된 query/fragment/ampersand-only GUID만 URL로 대체한다. 정상 publisher GUID와 기존 무 GUID 처리의 ID는 유지한다. URL의 추적 query만 제거하고 기능성 query를 보존한다. 잘못된 URL은 제목/날짜 fallback으로 feed 전체 실패를 피한다.

격리는 운영자가 확인한 오염에만 실행하는 별도 service이며, 미리 읽은 문서/이벤트/연결/영향 snapshot 지문을 잠금 안에서 다시 대조한다. 모든 변경 전 값을 기존 ops.pipeline_run.config_json에 원자적으로 보존하고 active impact edges만 제거한다. 문서/이벤트의 유형을 격리 상태로 바꾸며 원문/번역/청크/AI 출력 및 금융 기록은 삭제하지 않는다. 다른 source 문서를 함께 쓰는 이벤트는 거부한다. 격리 문서는 RSS 재수집으로 덮어쓰지 않는다.

남는 한계: 정상 ID로 같은 기사의 본문이 수정될 때 모든 파생 산출물을 버전 관리하는 일반 기능은 이번 범위가 아니다. 이미 여러 달 덮어쓴 원문 역사 전체를 복구하지 못하며, 해당 문서를 사용한 과거 리포트와 추천은 보존하므로 별도 내용 검토가 필요하다. 현재 AAPL artifact 493은 문서 22를 입력 목록에 포함하지만 핵심 주장/촉매에 직접 인용하지 않았다. 보고서 재생성이나 검토 통과 처리, 모델 호출, 추천 weight/benchmark/schema 변경은 하지 않는다.
