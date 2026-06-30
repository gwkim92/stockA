import Link from "next/link";
import { koCode } from "@/lib/korean-labels";
import type { RecommendationDetailData } from "@/lib/types";
import styles from "./recommendation-executive-brief.module.css";

type RecommendationExecutiveBriefProps = {
  data: RecommendationDetailData;
};

type BriefTone = "ready" | "watch" | "blocked";
type Metric = {
  readonly label: string;
  readonly value: string;
  readonly detail: string;
  readonly tone: BriefTone;
};

function formatRecommendationPercent(value: number | null, signDisplay?: "exceptZero") {
  if (value === null) {
    return "미측정";
  }
  return new Intl.NumberFormat("ko-KR", {
    style: "percent",
    maximumFractionDigits: 1,
    ...(signDisplay ? { signDisplay } : {}),
  }).format(value);
}

function formatRecommendationCurrency(value: number | null, currencyCode: string) {
  if (value === null) {
    return "데이터 없음";
  }
  return new Intl.NumberFormat("ko-KR", {
    style: "currency",
    currency: currencyCode,
    maximumFractionDigits: currencyCode === "KRW" ? 0 : 2,
  }).format(value);
}

function investorRecommendationText(value: string) {
  return value
    .replaceAll("페이퍼", "가상 매매")
    .replaceAll("valuation snapshot이", "목표가 자료가")
    .replaceAll("valuation snapshot", "목표가 자료")
    .replaceAll("목표가 자료이", "목표가 자료가")
    .replaceAll("professional analysis", "전문 분석")
    .replaceAll("레이어", "근거 항목");
}

function formatPercent(value: number | null) {
  return formatRecommendationPercent(value, "exceptZero");
}

function formatWeightPercent(value: number | null) {
  return formatRecommendationPercent(value);
}

function positionLabel(status: string) {
  if (status === "held") {
    return "보유 중";
  }
  if (status === "not_held") {
    return "미보유";
  }
  return "상태 보류";
}

function positionSummary(data: RecommendationDetailData) {
  const position = data.position_context;
  if (position.status === "held") {
    return `현재 비중 ${formatPercent(position.weight)} · 평단가 ${formatRecommendationCurrency(position.average_cost, position.currency_code)}`;
  }
  return `현재 비중 없음 · 추천 비중 ${formatWeightPercent(data.recommended_weight)}`;
}

function valuationSummary(data: RecommendationDetailData) {
  const valuation = data.valuation_target_range;
  if (valuation.status === "available") {
    return `기준 상승여지 ${formatPercent(valuation.upside_base)} · 안전마진 ${formatPercent(valuation.margin_of_safety)}`;
  }
  return investorRecommendationText(valuation.summary || "가치 범위 보강 필요").replaceAll("UNKNOWN", data.symbol);
}

function valuationValue(data: RecommendationDetailData) {
  const valuation = data.valuation_target_range;
  if (valuation.target_base !== null) {
    return formatRecommendationCurrency(valuation.target_base, valuation.currency_code);
  }
  if (valuation.base_price !== null) {
    return formatRecommendationCurrency(valuation.base_price, valuation.currency_code);
  }
  return "대기";
}

function isFundOrEtf(data: RecommendationDetailData) {
  return Boolean(data.fund_instrument_analysis) || data.professional_evidence_audit.product_type === "fund_or_etf";
}

function fundStatusLabel(status: string) {
  if (status === "collected" || status === "available") {
    return "수집 완료";
  }
  if (status === "missing") {
    return "데이터 없음";
  }
  if (status === "stale") {
    return "오래된 자료";
  }
  return investorRecommendationText(status);
}

function fundLensValue(data: RecommendationDetailData) {
  const fund = data.fund_instrument_analysis;
  if (!fund) {
    return "ETF 근거 대기";
  }
  return `${fund.holding_count.toLocaleString("ko-KR")}개 보유`;
}

function fundLensSummary(data: RecommendationDetailData) {
  const fund = data.fund_instrument_analysis;
  if (!fund) {
    return "ETF 보유종목, 비용률, 추적차이 자료가 아직 연결되지 않았다.";
  }
  return `커버리지 ${formatWeightPercent(fund.holdings_coverage_weight)} · 비용률 ${formatWeightPercent(fund.expense_ratio.value)} · 유동성 ${fundStatusLabel(fund.liquidity.status)}`;
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

function CompactMetric({
  label,
  value,
  detail,
  tone,
}: Metric) {
  return (
    <div className={`${styles.metric} ${toneClassName(tone)}`}>
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{detail}</small>
    </div>
  );
}

export function RecommendationExecutiveBrief({ data }: RecommendationExecutiveBriefProps) {
  const evidence = data.professional_evidence_audit;
  const decision = data.professional_decision_waterfall;
  const position = data.position_context;
  const fundOrEtf = isFundOrEtf(data);
  const hasOrderBlocked = !decision.broker_submit_allowed;
  const cleanText = (value: string) => investorRecommendationText(value).replaceAll("UNKNOWN", data.symbol);
  const evidenceSummary = cleanText(evidence.summary || decision.summary);
  const metrics: readonly Metric[] = [
    {
      label: "보유 현실",
      value: positionLabel(position.status),
      detail: positionSummary(data),
      tone: position.status === "held" ? "ready" : "watch",
    },
    {
      label: fundOrEtf ? "ETF 구조" : "가치 범위",
      value: fundOrEtf ? fundLensValue(data) : valuationValue(data),
      detail: fundOrEtf ? fundLensSummary(data) : valuationSummary(data),
      tone: fundOrEtf || data.valuation_target_range.status === "available" ? "ready" : "watch",
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
  ];

  return (
    <section className={styles.brief} aria-labelledby="recommendation-executive-brief-title">
      <div className={styles.main}>
        <div className={styles.header}>
          <span>{fundOrEtf ? "ETF 추천 결론" : "개별 주식 추천 결론"}</span>
          <h2 id="recommendation-executive-brief-title">{cleanText(evidence.title || `${data.symbol} 추천 판단`)}</h2>
          <p>{evidenceSummary}</p>
        </div>

        <div className={styles.decisionLine} aria-label="추천 상세 핵심 판단">
          <div>
            <span>추천</span>
            <strong>{koCode(data.recommendation)}</strong>
          </div>
          <div>
            <span>점수</span>
            <strong>{formatPercent(data.score)}</strong>
          </div>
          <div>
            <span>포지션</span>
            <strong>{positionLabel(position.status)}</strong>
          </div>
          <div>
            <span>실거래</span>
            <strong>{hasOrderBlocked ? "차단" : "허용"}</strong>
          </div>
        </div>
      </div>

      <aside className={styles.readingPath} aria-label="이 추천서를 읽는 순서">
        <span>읽는 순서</span>
        <ol>
          <li>보유 여부와 평단가를 먼저 본다.</li>
          <li>{fundOrEtf ? "보유 구성·비용·추적 품질을 대조한다." : "가치 범위와 재무 근거를 대조한다."}</li>
          <li>근거 품질과 주문 차단 여부를 마지막에 대조한다.</li>
        </ol>
      </aside>

      <div className={styles.metricStrip}>
        {metrics.map((metric) => (
          <CompactMetric key={metric.label} {...metric} />
        ))}
      </div>

      <div className={styles.actions}>
        <Link href={`/stocks/${encodeURIComponent(data.symbol)}`}>종목 리서치</Link>
        <Link href="#recommendation-position-reality">포지션 확인</Link>
        <Link href={fundOrEtf ? "#recommendation-fund-analysis" : "#recommendation-valuation"}>
          {fundOrEtf ? "ETF 근거" : "밸류에이션"}
        </Link>
        <Link href="/paper-trading">가상 매매</Link>
        <Link href="#recommendation-professional-flow">전문 분석 흐름</Link>
      </div>
    </section>
  );
}
