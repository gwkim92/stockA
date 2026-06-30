import { brokerOrderBoundaryLabel } from "@/lib/presentation";
import type { RecommendationPositionReference } from "@/lib/types";

import styles from "./recommendation-position-reality.module.css";

function formatQuantity(value: number | null) {
  if (value === null) {
    return "없음";
  }
  return new Intl.NumberFormat("ko-KR", {
    maximumFractionDigits: value < 1 ? 6 : 2,
  }).format(value);
}

function formatCurrency(value: number | null, currencyCode: string) {
  if (value === null) {
    return "데이터 없음";
  }
  return new Intl.NumberFormat("ko-KR", {
    style: "currency",
    currency: currencyCode,
    maximumFractionDigits: currencyCode === "KRW" ? 0 : 2,
  }).format(value);
}

function priceCurrency(position: RecommendationPositionReference) {
  return position.native_currency_code || position.currency_code;
}

function marketPrice(position: RecommendationPositionReference) {
  if (position.market_price_native !== null) {
    return {
      value: position.market_price_native,
      currencyCode: priceCurrency(position),
    };
  }
  return {
    value: position.market_price,
    currencyCode: position.currency_code,
  };
}

function positionStatusLabel(status: string) {
  if (status === "held") {
    return "보유 중";
  }
  if (status === "not_held") {
    return "보유 없음";
  }
  return "상태 보류";
}

function hasOpenPosition(position: RecommendationPositionReference) {
  return position.status === "held" && position.quantity !== null && position.quantity !== 0;
}

function portfolioDisplayName(name: string) {
  if (name === "Long Term Paper") {
    return "장기 가상 포트폴리오";
  }
  if (name === "Toss Real Readonly") {
    return "토스 실계좌 읽기 전용";
  }
  return name;
}

function BrokerMetric({
  label,
  note,
  value,
}: {
  readonly label: string;
  readonly note: string;
  readonly value: string;
}) {
  return (
    <div className={styles.metric}>
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{note}</small>
    </div>
  );
}

export function RecommendationBrokerReality({
  brokerSubmitAllowed,
  orderBoundary,
  position,
}: {
  readonly brokerSubmitAllowed: boolean;
  readonly orderBoundary: string;
  readonly position: RecommendationPositionReference;
}) {
  const price = marketPrice(position);
  const hasPosition = hasOpenPosition(position);
  return (
    <aside className={styles.broker}>
      <div>
        <span>토스증권 브로커 현실</span>
        <strong>{portfolioDisplayName(position.portfolio_name)}</strong>
        <p>
          읽기 전용 계좌 기준 {positionStatusLabel(position.status)} 상태다. 이 값은 보유 현실과 가상 매매 검증에는
          쓰지만 추천 점수 자체를 바꾸지는 않는다.
        </p>
      </div>
      <div className={styles.brokerMetrics}>
        <BrokerMetric label="보유 수량" value={formatQuantity(position.quantity)} note={position.snapshot_date ?? "스냅샷 없음"} />
        <BrokerMetric
          label="브로커 가격"
          value={hasPosition ? formatCurrency(price.value, price.currencyCode) : "해당 없음"}
          note={hasPosition ? position.native_currency_code : "미보유 계좌"}
        />
        <BrokerMetric
          label="주문 제출"
          value={brokerSubmitAllowed ? "허용" : "차단"}
          note={brokerOrderBoundaryLabel(orderBoundary)}
        />
        <BrokerMetric
          label="원천 실행"
          value={position.source_run_id ? "계좌 원장 연결" : "원천 대기"}
          note={position.source_run_id ?? "계좌 스냅샷 원천 없음"}
        />
      </div>
    </aside>
  );
}
