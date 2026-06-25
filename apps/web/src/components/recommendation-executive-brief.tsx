import Link from "next/link";
import type { RecommendationDetailData } from "@/lib/types";
import styles from "./recommendation-executive-brief.module.css";

type RecommendationExecutiveBriefProps = {
  data: RecommendationDetailData;
};

type BriefTone = "ready" | "watch" | "blocked";

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

function positionLabel(status: string) {
  if (status === "held") {
    return "보유 중";
  }
  if (status === "not_held") {
    return "미보유";
  }
  return "확인 필요";
}

function positionSummary(data: RecommendationDetailData) {
  const position = data.position_context;
  if (position.status === "held") {
    return `현재 비중 ${formatPercent(position.weight)} · 평단가 ${formatCurrency(position.average_cost, position.currency_code)}`;
  }
  return `현재 비중 없음 · 추천 비중 ${formatWeightPercent(data.recommended_weight)}`;
}

function valuationSummary(data: RecommendationDetailData) {
  const valuation = data.valuation_target_range;
  if (valuation.status === "available") {
    return `기준 상승여지 ${formatPercent(valuation.upside_base)} · 안전마진 ${formatPercent(valuation.margin_of_safety)}`;
  }
  return valuation.summary || "가치 범위 보강 필요";
}

function valuationValue(data: RecommendationDetailData) {
  const valuation = data.valuation_target_range;
  if (valuation.target_base !== null) {
    return formatCurrency(valuation.target_base, valuation.currency_code);
  }
  if (valuation.base_price !== null) {
    return formatCurrency(valuation.base_price, valuation.currency_code);
  }
  return "대기";
}

function evidenceTone(data: RecommendationDetailData): BriefTone {
  const audit = data.professional_evidence_audit;
  if (audit.source_blocker.blocked || audit.blocked_layer_count > 0) {
    return "blocked";
  }
  if (audit.missing_layer_count > 0 || audit.pending_layer_count > 0) {
    return "watch";
  }
  return "ready";
}

function tradeTone(data: RecommendationDetailData): BriefTone {
  const decision = data.professional_decision_waterfall;
  if (decision.broker_submit_allowed) {
    return "ready";
  }
  if (decision.paper_validation_input_allowed) {
    return "watch";
  }
  return "blocked";
}

function toneClassName(tone: BriefTone) {
  if (tone === "ready") {
    return styles.ready;
  }
  if (tone === "blocked") {
    return styles.blocked;
  }
  return styles.watch;
}

function BriefCard({
  label,
  value,
  detail,
  tone,
}: {
  label: string;
  value: string;
  detail: string;
  tone: BriefTone;
}) {
  return (
    <div className={`${styles.card} ${toneClassName(tone)}`}>
      <span>{label}</span>
      <strong>{value}</strong>
      <p>{detail}</p>
    </div>
  );
}

export function RecommendationExecutiveBrief({ data }: RecommendationExecutiveBriefProps) {
  const evidence = data.professional_evidence_audit;
  const decision = data.professional_decision_waterfall;
  const position = data.position_context;
  const hasOrderBlocked = !decision.broker_submit_allowed;
  const cards = [
    {
      label: "현재 판정",
      value: evidence.title || "추천 검토",
      detail: evidence.summary || decision.summary,
      tone: evidenceTone(data),
    },
    {
      label: "포지션",
      value: positionLabel(position.status),
      detail: positionSummary(data),
      tone: position.status === "held" ? "ready" : "watch",
    },
    {
      label: "가치 범위",
      value: valuationValue(data),
      detail: valuationSummary(data),
      tone: data.valuation_target_range.status === "available" ? "ready" : "watch",
    },
    {
      label: "근거 품질",
      value: `${evidence.available_layer_count}/${evidence.expected_layer_count}개 충족`,
      detail:
        evidence.missing_layer_count > 0
          ? `보강 필요 ${evidence.missing_layer_count}개 · 차단 ${evidence.blocked_layer_count}개`
          : "전문 근거 레이어가 연결됐다.",
      tone: evidenceTone(data),
    },
    {
      label: "거래 경계",
      value: hasOrderBlocked ? "실거래 차단" : "주문 가능",
      detail: decision.paper_validation_input_allowed ? "가상 매매 입력 가능 · 실거래는 별도 승인 필요" : "가상 매매 입력 전 보강 필요",
      tone: tradeTone(data),
    },
  ] satisfies Array<{
    label: string;
    value: string;
    detail: string;
    tone: BriefTone;
  }>;

  return (
    <section className={styles.brief} aria-labelledby="recommendation-executive-brief-title">
      <div className={styles.header}>
        <span>투자 판단 요약</span>
        <h2 id="recommendation-executive-brief-title">{data.symbol} 추천을 한 화면에서 먼저 판정한다</h2>
        <p>
          점수, 보유 상태, 가치 범위, 근거 품질, 거래 경계를 먼저 대조한다. 자세한 뉴스·사이클·재무 근거는 아래 리포트에서 이어서 확인한다.
        </p>
      </div>
      <div className={styles.cards}>
        {cards.map((card) => (
          <BriefCard key={card.label} {...card} />
        ))}
      </div>
      <div className={styles.actions}>
        <Link href="#recommendation-position-reality">포지션 확인</Link>
        <Link href="#recommendation-valuation">밸류에이션</Link>
        <Link href="#recommendation-professional-flow">전문 분석 흐름</Link>
      </div>
    </section>
  );
}
