import { finiteNumber, memoCurrency, memoPositionLabel } from "@/lib/recommendation-memo-model";
import { brokerOrderBoundaryLabel } from "@/lib/presentation";
import type { RecommendationPositionReference } from "@/lib/types";

import styles from "./recommendation-position-reality.module.css";

function formatQuantity(value: number | null) {
  if (value === null || !Number.isFinite(value)) {
    return "미확인";
  }
  return new Intl.NumberFormat("ko-KR", {
    maximumFractionDigits: value < 1 ? 6 : 2,
  }).format(value);
}

function formatCurrency(value: number | null, currencyCode: string) {
  return memoCurrency(value, currencyCode);
}

function priceCurrency(position: RecommendationPositionReference) {
  return position.native_currency_code || position.currency_code;
}

function marketPrice(position: RecommendationPositionReference) {
  if (finiteNumber(position.market_price_native) !== null) {
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
  return memoPositionLabel(status);
}

function hasOpenPosition(position: RecommendationPositionReference) {
  return position.status === "held" && finiteNumber(position.quantity) !== null && position.quantity !== 0;
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
          읽기 전용 계좌 기준 {positionStatusLabel(position.status)} 상태입니다. 이 값은 보유 현실과 가상 매매
          검증에만 쓰이며 추천 점수는 바꾸지 않습니다.
        </p>
      </div>
      <div className={styles.brokerMetrics}>
        <BrokerMetric label="보유 수량" value={formatQuantity(position.quantity)} note={position.snapshot_date ?? "스냅샷 없음"} />
        <BrokerMetric
          label="브로커 가격"
          value={hasPosition ? formatCurrency(price.value, price.currencyCode) : position.status === "not_held" ? "해당 없음" : "미확인"}
          note={hasPosition ? position.native_currency_code : position.status === "not_held" ? "미보유 계좌" : "보유 원장 확인 필요"}
        />
        <BrokerMetric
          label="주문 제출"
          value={brokerSubmitAllowed ? "허용" : "차단"}
          note={brokerOrderBoundaryLabel(orderBoundary)}
        />
        <BrokerMetric
          label="계좌 스냅샷"
          value={position.source_run_id ? "연결됨" : "대기"}
          note={
            position.snapshot_date
              ? `${position.snapshot_date} 기준 토스증권 읽기 전용 원장`
              : "토스증권 원장 스냅샷 대기"
          }
        />
      </div>
    </aside>
  );
}
