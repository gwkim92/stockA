# Session Handoff

## Current Status

- 진행 중: task contract를 만들었고, State Street 공식 SPY daily holdings XLSX를 benchmark composition import로 연결하는 backend CLI를 구현한다.

## Implementation Notes

- 공식 source 후보: `https://www.ssga.com/library-content/products/fund-data/etfs/us/holdings-daily-us-en-spy.xlsx`
- State Street SPY page는 `Download All Holdings: Daily` 링크를 제공한다.
- raw XLSX와 normalized CSV는 repo 밖 runtime/artifact 경로에 저장해야 한다.
- 추천 weight와 주문 경로는 절대 변경하지 않는다.

## Verification

- 아직 실행 전.

## Guardrails

- 추천 weight 변경 금지.
- benchmark/evaluation split 변경 금지.
- broker submit, live order, kill switch unlock 금지.
- repo 안 secret/env 값 수정 금지.

## Exact Next Step

- exact next step: provider XLSX parser와 `benchmark-composition-ssga-spdr-import-run` CLI를 구현한다.
