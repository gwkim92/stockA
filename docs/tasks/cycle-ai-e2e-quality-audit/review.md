# Review

## Result

- 품질 감사는 recommendation weight를 바꾸지 않고 읽기/감사/reporting 계층으로 추가됐다.

## Remaining Risk

- direct ticker grounding은 원문 제목/요약의 symbol 또는 회사명 첫 단어 기반이다. 뉴스 본문 전문 grounding이나 alias dictionary는 다음 eval dataset task에서 보강해야 한다.
- duplicate title check는 제목 기준이다. URL canonicalization과 semantic duplicate는 다음 단계에서 보강해야 한다.
