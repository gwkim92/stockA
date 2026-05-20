# Free Market Data Provider Strategy Plan

## Steps

1. Alpha Vantage 공식 무료 한도와 현재 local ledger 설정을 분리한다.
2. 무료 또는 no-cost trial 후보를 공식 자료 중심으로 비교한다.
3. broad universe용 첫 pilot provider를 선택한다.
4. Alpha Vantage의 역할을 fallback으로 재정의한다.
5. local-live-mvp-runtime handoff에 다음 구현 순서를 남긴다.

## Non-Goals

- 새 provider API key 발급
- 실제 provider 호출
- DB schema 변경
- 가격 adapter 구현
- trading/order flow
