import Link from "next/link";
import type { RecommendationDetailData, RecommendationPositionReference } from "@/lib/types";
import styles from "./recommendation-position-reality.module.css";

type RecommendationPositionRealityProps = {
  data: RecommendationDetailData;
};

function formatQuantity(value: number | null) {
  if (value === null) {
    return "없음";
  }
  return new Intl.NumberFormat("ko-KR", {
    maximumFractionDigits: value < 1 ? 6 : 2,
  }).format(value);
}

function formatPercent(value: number | null) {
  if (value === null) {
    return "미측정";
  }
  return new Intl.NumberFormat("ko-KR", {
    style: "percent",
    maximumFractionDigits: 1,
    signDisplay: "exceptZero",
  }).format(value);
}

function formatWeightPercent(value: number | null) {
  if (value === null) {
    return "미측정";
  }
  return new Intl.NumberFormat("ko-KR", {
    style: "percent",
    maximumFractionDigits: 1,
  }).format(value);
}

function formatCurrency(value: number | null, currencyCode: string) {
  if (value === null) {
    return "미수집";
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

function averageCost(position: RecommendationPositionReference) {
  if (position.cost_basis_native !== null && position.quantity !== null && position.quantity !== 0) {
    return {
      value: position.cost_basis_native / position.quantity,
      currencyCode: priceCurrency(position),
    };
  }
  return {
    value: position.average_cost,
    currencyCode: position.currency_code,
  };
}

function averageCostNote(position: RecommendationPositionReference) {
  if (position.status === "not_held") {
    return "미보유라 취득원가 없음";
  }
  if (position.average_cost !== null || position.cost_basis_native !== null) {
    return "원장 기준";
  }
  return "취득원가 필요";
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
  return "상태 확인 필요";
}

function positionTone(status: string) {
  if (status === "held") {
    return styles.held;
  }
  if (status === "not_held") {
    return styles.empty;
  }
  return styles.watch;
}

function hasOpenPosition(position: RecommendationPositionReference) {
  return position.status === "held" && position.quantity !== null && position.quantity !== 0;
}

function holdingCurrencyValue(
  position: RecommendationPositionReference,
  value: number | null,
  currencyCode: string,
) {
  if (!hasOpenPosition(position)) {
    return "해당 없음";
  }
  return formatCurrency(value, currencyCode);
}

function holdingMetricNote(position: RecommendationPositionReference, heldNote: string) {
  if (!hasOpenPosition(position)) {
    return "미보유라 계산하지 않음";
  }
  return heldNote;
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

function Metric({
  label,
  value,
  note,
}: {
  label: string;
  value: string;
  note: string;
}) {
  return (
    <div className={styles.metric}>
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{note}</small>
    </div>
  );
}

function BrokerReference({ position }: { position: RecommendationPositionReference }) {
  const price = marketPrice(position);
  const hasPosition = hasOpenPosition(position);
  return (
    <aside className={styles.broker}>
      <div>
        <span>브로커 계좌</span>
        <strong>{portfolioDisplayName(position.portfolio_name)}</strong>
        <p>{positionStatusLabel(position.status)}</p>
      </div>
      <div className={styles.brokerMetrics}>
        <Metric label="보유 수량" value={formatQuantity(position.quantity)} note={position.snapshot_date ?? "스냅샷 없음"} />
        <Metric
          label="브로커 가격"
          value={hasPosition ? formatCurrency(price.value, price.currencyCode) : "해당 없음"}
          note={hasPosition ? position.native_currency_code : "미보유 계좌"}
        />
      </div>
    </aside>
  );
}

export function RecommendationPositionReality({ data }: RecommendationPositionRealityProps) {
  const position = data.position_context;
  const avg = averageCost(position);
  const price = marketPrice(position);
  const tone = positionTone(position.status);
  const actionText =
    position.status === "held"
      ? "기존 보유 포지션과 추천 방향이 충돌하는지 확인합니다."
      : "현재 보유가 없으므로 신규 편입 후보로만 검토합니다.";

  return (
    <section
      className={`${styles.panel} ${tone}`}
      id="recommendation-position-reality"
      aria-labelledby="recommendation-position-reality-title"
    >
      <div className={styles.lead}>
        <span>포지션 현실</span>
        <h2 id="recommendation-position-reality-title">
          {data.symbol} · {positionStatusLabel(position.status)}
        </h2>
        <p>{position.summary}</p>
        <div className={styles.actions}>
          <Link href="/portfolio/coverage">보유 현황 보기</Link>
          <Link href="/paper-trading">가상 매매 상태</Link>
        </div>
      </div>

      <div className={styles.metrics} aria-label="추천 종목 보유 포지션과 평단가">
        <Metric label="포트폴리오" value={portfolioDisplayName(position.portfolio_name)} note={position.snapshot_date ?? "스냅샷 없음"} />
        <Metric label="보유 수량" value={formatQuantity(position.quantity)} note={actionText} />
        <Metric label="평단가" value={holdingCurrencyValue(position, avg.value, avg.currencyCode)} note={averageCostNote(position)} />
        <Metric
          label="현재가"
          value={holdingCurrencyValue(position, price.value, price.currencyCode)}
          note={holdingMetricNote(position, "포지션 스냅샷 기준")}
        />
        <Metric
          label="평가금액"
          value={holdingCurrencyValue(position, position.market_value, position.currency_code)}
          note={hasOpenPosition(position) ? `비중 ${formatPercent(position.weight)}` : "미보유"}
        />
        <Metric
          label="평가손익"
          value={holdingCurrencyValue(position, position.unrealized_pnl, position.currency_code)}
          note={hasOpenPosition(position) ? formatPercent(position.unrealized_pnl_pct) : "미보유"}
        />
        <Metric label="추천 비중" value={formatWeightPercent(data.recommended_weight)} note="점수와 분리된 목표 비중" />
        <Metric label="주문 경계" value={position.broker_submit_allowed ? "주문 허용" : "실거래 차단"} note="읽기 전용" />
      </div>

      <BrokerReference position={position.broker_reference} />
    </section>
  );
}
