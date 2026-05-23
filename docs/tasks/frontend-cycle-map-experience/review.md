# Review Notes

- 이 작업은 read-only 화면과 DTO 추가다.
- cycle summary 생성, 추천 산식, 거래 안전 정책은 변경하지 않는다.
- 대표 종목 링크는 사람이 클릭하는 핵심 경로이므로 생성형 요약 artifact가 아니라 canonical exposure/propagation 테이블을 기준으로 계산해야 한다.
- 직접 종목 impact는 원문에 티커나 회사명 grounding이 없으면 validator에서 차단한다. 거시/테마 뉴스는 직접 종목이 아니라 상위 흐름 전파로 내려보내는 것이 맞다.
