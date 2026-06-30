export type BrokerDataUseInput = {
  readonly used_for_account: boolean;
  readonly used_for_execution: boolean;
  readonly used_for_scoring: boolean;
};

export function brokerDataUseLabel(input: BrokerDataUseInput): string {
  if (input.used_for_execution) {
    return "실행 가격 후보";
  }
  if (input.used_for_scoring) {
    return "추천 점수 반영";
  }
  if (input.used_for_account) {
    return "계좌 검증";
  }
  return "브로커 참고";
}

export function brokerOrderBoundaryLabel(value: string | null | undefined): string {
  if (value === "read_only_no_order") {
    return "읽기 전용, 실거래 주문 차단";
  }
  if (!value) {
    return "주문 경계 미기록";
  }
  return value;
}

export function formatBasisPointDiff(value: number | null | undefined): string {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return "미측정";
  }
  return `${value.toLocaleString("ko-KR", { maximumFractionDigits: 3 })}bp`;
}
