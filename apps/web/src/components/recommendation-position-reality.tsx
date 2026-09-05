import Link from "next/link";
import { finiteNumber, memoCurrency, memoPositionLabel } from "@/lib/recommendation-memo-model";
import type { RecommendationDetailData, RecommendationPositionReference } from "@/lib/types";
import { RecommendationBrokerReality } from "./recommendation-broker-reality";
import styles from "./recommendation-position-reality.module.css";

type RecommendationPositionRealityProps = {
  data: RecommendationDetailData;
};

function formatQuantity(value: number | null) {
  if (value === null || !Number.isFinite(value)) {
    return "미확인";
  }
  return new Intl.NumberFormat("ko-KR", {
    maximumFractionDigits: value < 1 ? 6 : 2,
  }).format(value);
}

function formatPercent(value: number | null | undefined) {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return "미측정";
  }
  return new Intl.NumberFormat("ko-KR", {
    style: "percent",
    maximumFractionDigits: 1,
    signDisplay: "exceptZero",
  }).format(value);
}

function formatWeightPercent(value: number | null | undefined) {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return "미측정";
  }
  return new Intl.NumberFormat("ko-KR", {
    style: "percent",
    maximumFractionDigits: 1,
  }).format(value);
}

function formatCurrency(value: number | null, currencyCode: string) {
  return memoCurrency(value, currencyCode);
}

function priceCurrency(position: RecommendationPositionReference) {
  return position.native_currency_code || position.currency_code;
}

function averageCost(position: RecommendationPositionReference) {
  if (finiteNumber(position.cost_basis_native) !== null && finiteNumber(position.quantity) !== null && position.quantity !== 0) {
    return {
      value: (position.cost_basis_native as number) / (position.quantity as number),
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
  if (position.status !== "held") return "보유 원장 확인 필요";
  if (finiteNumber(position.average_cost) !== null || finiteNumber(position.cost_basis_native) !== null) {
    return "원장 기준";
  }
  return "취득원가 필요";
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
  return position.status === "held" && finiteNumber(position.quantity) !== null && position.quantity !== 0;
}

function positionSummary(symbol: string, position: RecommendationPositionReference) {
  if (position.status === "held") {
    return `${symbol}은 이미 보유 중입니다. 평단가, 현재가, 평가손익을 추천 방향과 함께 대조합니다.`;
  }
  if (position.status === "not_held") {
    return `${symbol}은 현재 보유하지 않습니다. 신규 편입 후보 조건과 안전 차단 상태를 먼저 분리합니다.`;
  }
  return `${symbol} 포지션 상태가 명확하지 않습니다. 보유 원장과 가상 매매 상태를 함께 대조합니다.`;
}

function holdingCurrencyValue(
  position: RecommendationPositionReference,
  value: number | null,
  currencyCode: string,
) {
  if (position.status === "not_held") return "해당 없음";
  if (!hasOpenPosition(position)) return "미확인";
  return formatCurrency(value, currencyCode);
}

function holdingMetricNote(position: RecommendationPositionReference, heldNote: string) {
  if (position.status === "not_held") return "미보유라 계산하지 않음";
  if (!hasOpenPosition(position)) return "보유 원장 확인 필요";
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

export function RecommendationPositionReality({ data }: RecommendationPositionRealityProps) {
  const position = data.position_context;
  const avg = averageCost(position);
  const price = marketPrice(position);
  const tone = positionTone(position.status);
  const actionText =
    position.status === "held"
      ? "보유 수량과 추천 방향의 충돌 여부"
      : position.status === "not_held" ? "신규 편입 후보 상태" : "보유 원장 확인 필요";

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
        <p>{positionSummary(data.symbol, position)}</p>
        <div className={styles.actions}>
          <Link href="/portfolio/coverage">보유 현황 보기</Link>
          <Link href="/paper-trading">가상 매매 상태</Link>
        </div>
      </div>

      <div className={styles.ledgerSummary} aria-label="포지션 요약">
        <div>
          <span>포트폴리오</span>
          <strong>{portfolioDisplayName(position.portfolio_name)}</strong>
          <small>{position.snapshot_date ?? "스냅샷 없음"}</small>
        </div>
        <div>
          <span>주문 경계</span>
          <strong>{position.broker_submit_allowed ? "주문 허용" : "실거래 차단"}</strong>
          <small>읽기 전용</small>
        </div>
      </div>

      <div className={styles.metrics} aria-label="추천 종목 보유 포지션과 평단가">
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
          note={hasOpenPosition(position) ? `비중 ${formatPercent(position.weight)}` : position.status === "not_held" ? "미보유" : "보유 원장 확인 필요"}
        />
        <Metric
          label="평가손익"
          value={holdingCurrencyValue(position, position.unrealized_pnl, position.currency_code)}
          note={hasOpenPosition(position) ? formatPercent(position.unrealized_pnl_pct) : position.status === "not_held" ? "미보유" : "보유 원장 확인 필요"}
        />
        <Metric label="추천 비중" value={formatWeightPercent(data.recommended_weight)} note="점수와 분리된 목표 비중" />
      </div>

      <RecommendationBrokerReality
        brokerSubmitAllowed={position.broker_submit_allowed}
        orderBoundary={position.order_boundary}
        position={position.broker_reference}
      />
    </section>
  );
}
