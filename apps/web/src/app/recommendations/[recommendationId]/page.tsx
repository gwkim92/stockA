import Link from "next/link";
import type { Route } from "next";
import { AuditMetadata, type AuditMetadataItem } from "@/components/audit-metadata";
import { NewsTitleBlock } from "@/components/news-title-block";
import { getRecommendationDetail } from "@/lib/frontend-api";
import { koCode, koLabel } from "@/lib/korean-labels";
import type { RecommendationDetailData } from "@/lib/types";

export const dynamic = "force-dynamic";
export const metadata = { title: "추천 상세" };

type RecommendationPageProps = {
  params: Promise<{ recommendationId: string }>;
};

function formatPercent(value: number) {
  return `${Math.round(value * 1000) / 10}%`;
}

type ScoreComponent = RecommendationDetailData["score_components"][number];

function macroFlowRows(component: ScoreComponent) {
  if (component.provenance?.source_type !== "macro_flow_propagation") {
    return [];
  }
  return component.provenance.evidence?.recent_flows ?? [];
}

function themeHref(themeKey: string | null | undefined) {
  return themeKey ? (`/themes/${encodeURIComponent(themeKey)}` as Route) : null;
}

function formatMetricValue(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return "값 없음";
  }
  if (Math.abs(value) < 1) {
    return formatPercent(value);
  }
  return value.toLocaleString("ko-KR", { maximumFractionDigits: 4 });
}

function provenanceBadges(component: ScoreComponent) {
  const provenance = component.provenance;
  if (!provenance) {
    return ["출처 요약 대기"];
  }

  const badges = [koCode(provenance.source_type)];
  if (provenance.feature_code) {
    badges.push(koCode(provenance.feature_code));
  }
  if (provenance.rank_position !== null && provenance.rank_position !== undefined) {
    badges.push(
      provenance.universe_member_count
        ? `유니버스 ${provenance.rank_position}/${provenance.universe_member_count}위`
        : `유니버스 ${provenance.rank_position}위`,
    );
  }
  if (provenance.evidence?.first_trade_date && provenance.evidence.latest_trade_date) {
    badges.push(`${provenance.evidence.first_trade_date}~${provenance.evidence.latest_trade_date}`);
  } else if (provenance.latest_trade_date) {
    badges.push(`최근 가격일 ${provenance.latest_trade_date}`);
  }
  if (provenance.source_type === "macro_flow_propagation") {
    badges.push(`전파 근거 ${provenance.evidence?.propagated_impact_count ?? 0}개`);
  }
  return badges;
}

function provenanceMetadata(component: ScoreComponent): AuditMetadataItem[] {
  const provenance = component.provenance;
  if (!provenance) {
    return [
      { label: "점수 구성요소", value: component.component },
      { label: "근거 ID", value: component.evidence_id },
    ];
  }

  return [
    { label: "점수 구성요소", value: component.component },
    { label: "근거 ID", value: component.evidence_id },
    { label: "출처 유형", value: provenance.source_type },
    { label: "출처 라벨", value: provenance.label },
    { label: "가격 지표 코드", value: provenance.feature_code },
    { label: "가격 지표 이름", value: provenance.feature_name },
    { label: "기준일", value: provenance.as_of_date },
    { label: "원천 실행 ID", value: provenance.source_run_id },
    { label: "유니버스 배치", value: provenance.universe_batch_id },
    { label: "가격 지표 버전", value: provenance.evidence?.feature_set_version },
    { label: "유니버스 순위", value: provenance.rank_position },
    { label: "유니버스 종목 수", value: provenance.universe_member_count },
    { label: "관측치 수", value: provenance.observation_count ?? provenance.evidence?.observation_count },
    { label: "첫 가격일", value: provenance.evidence?.first_trade_date },
    { label: "최근 가격일", value: provenance.latest_trade_date ?? provenance.evidence?.latest_trade_date },
    { label: "전파 근거 수", value: provenance.evidence?.propagated_impact_count },
    { label: "선정 규칙", value: provenance.selection_rule },
    { label: "편입 사유", value: provenance.inclusion_reason },
  ];
}

function provenanceDetail(component: ScoreComponent) {
  const provenance = component.provenance;
  if (!provenance) {
    return "아직 이 점수의 입력 출처 요약이 붙지 않았다.";
  }
  if (provenance.source_type === "market_feature") {
    const featureName = provenance.feature_code ? koCode(provenance.feature_code) : koCode(provenance.feature_name ?? "market_feature");
    return `${featureName}: 원값 ${formatMetricValue(provenance.feature_value)}, 표준화 점수 ${formatMetricValue(provenance.zscore)}.`;
  }
  if (provenance.source_type === "strategy_universe_rank") {
    const rankText =
      provenance.rank_position !== null && provenance.rank_position !== undefined
        ? `전략 유니버스 ${provenance.rank_position}${provenance.universe_member_count ? `/${provenance.universe_member_count}` : ""}위`
        : "전략 유니버스 순위";
    const observationText = provenance.observation_count ? `가격 관측치 ${provenance.observation_count}개` : "저장된 가격 관측치";
    return `${rankText}와 ${observationText}를 점수 입력으로 사용했다.`;
  }
  if (provenance.source_type === "event_or_ai_evidence") {
    return "뉴스, 공시, AI 구조화 결과와 연결된 정성 근거다.";
  }
  if (provenance.source_type === "macro_flow_propagation") {
    const count = provenance.evidence?.propagated_impact_count ?? 0;
    const firstFlow = provenance.evidence?.recent_flows?.[0];
    const flowText = firstFlow ? `${koCode(firstFlow.theme_key)} ${koCode(firstFlow.impact_direction)}` : "상위 흐름";
    return `${flowText} 등 ${count}개 전파 근거를 추천 점수 입력으로 사용했다.`;
  }
  return koLabel(provenance.label);
}

function evidenceHref(evidenceId: string, symbol: string) {
  if (evidenceId.startsWith("ai-evidence-")) {
    return `/ai-evidence/${evidenceId}` as Route;
  }
  if (evidenceId.startsWith("event-") || evidenceId.startsWith("sec-event-")) {
    return `/events?symbol=${encodeURIComponent(symbol)}` as Route;
  }
  if (evidenceId.startsWith("macro-flow-")) {
    return `/stocks/${encodeURIComponent(symbol)}` as Route;
  }
  return null;
}

function evidenceLinkLabel(evidenceId: string) {
  if (evidenceId.startsWith("ai-evidence-")) {
    return "AI 근거 열기";
  }
  if (evidenceId.startsWith("event-") || evidenceId.startsWith("sec-event-")) {
    return "이벤트 원장 열기";
  }
  if (evidenceId.startsWith("macro-flow-")) {
    return "종목 상세에서 흐름 보기";
  }
  return "근거 화면 열기";
}

function portfolioCoverageHref(reviewDate: string | null | undefined) {
  if (reviewDate) {
    return `/portfolio/coverage?asOfDate=${encodeURIComponent(reviewDate)}` as Route;
  }
  return "/portfolio/coverage" as Route;
}

function reviewCount(value: number | boolean | undefined) {
  return typeof value === "number" ? value : value ? 1 : 0;
}

function gateStatusLabel(status: string) {
  if (status === "pass") {
    return "통과";
  }
  if (status === "warning") {
    return "주의";
  }
  if (status === "blocked") {
    return "차단";
  }
  return koCode(status);
}

function gateStatusColor(status: string) {
  if (status === "pass") {
    return "var(--accent-green)";
  }
  if (status === "warning") {
    return "var(--accent-yellow)";
  }
  if (status === "blocked") {
    return "var(--accent-red)";
  }
  return "var(--text-secondary)";
}

function recommendationQualityDecision(data: RecommendationDetailData) {
  const blockedCount = reviewCount(data.evidence_review.summary.blocked_count);
  const warningCount = reviewCount(data.evidence_review.summary.warning_count);
  const adverseRecommendation = ["avoid", "exclude", "sell", "exit"].includes(data.recommendation);
  const weakScore = data.score < 0.35;
  const outcomeMeasured = data.outcome.label !== "unmeasured" && Boolean(data.outcome.measurement_end_date);
  const negativeAlpha = outcomeMeasured && data.outcome.alpha < 0;

  if (blockedCount > 0) {
    return {
      status: "검토 차단",
      tone: "risk-high",
      summary: "연결된 투자 논리, 점수 구성요소, 성과 측정 중 차단 조건이 있어 투자 검토로 넘기면 안 된다.",
    };
  }
  if (adverseRecommendation || weakScore) {
    return {
      status: "투자 보류",
      tone: "risk-high",
      summary: "현재 추천 조치나 점수가 중장기 신규 투자 후보로 보기 어렵다. 근거는 보존하되 채택하지 않는다.",
    };
  }
  if (warningCount > 0 || negativeAlpha || !outcomeMeasured) {
    return {
      status: "보강 후 검토",
      tone: "risk-medium",
      summary: "핵심 근거는 있으나 성과 측정, 근거 연결, 또는 최근 성과가 충분히 강하지 않아 사람 검토가 먼저다.",
    };
  }
  return {
    status: "사람 검토 가능",
    tone: "risk-low",
    summary: "근거와 성과가 연결되어 있어 중장기 투자 후보로 사람 검토를 진행할 수 있다.",
  };
}

function recommendationQualityChecks(data: RecommendationDetailData) {
  const outcomeMeasured = data.outcome.label !== "unmeasured" && Boolean(data.outcome.measurement_end_date);
  const aiEvidenceCount = reviewCount(data.evidence_review.summary.ai_evidence_component_count);
  const marketProvenanceCount = reviewCount(data.evidence_review.summary.market_or_rank_provenance_count);
  return [
    {
      label: "점수 강도",
      value: data.score >= 0.65 ? "강함" : data.score >= 0.35 ? "관찰 가능" : "약함",
      detail: `현재 점수 ${formatPercent(data.score)} · 추천 조치 ${koCode(data.recommendation)}`,
    },
    {
      label: "근거 연결",
      value: data.evidence_review.quality_status === "ready_for_human_review" ? "사람 검토 가능" : koCode(data.evidence_review.quality_status),
      detail: `AI/이벤트 근거 ${aiEvidenceCount}개 · 가격/순위 출처 기록 ${marketProvenanceCount}개`,
    },
    {
      label: "성과 확인",
      value: outcomeMeasured ? koCode(data.outcome.label) : "성과 미측정",
      detail: outcomeMeasured
        ? `알파 ${formatPercent(data.outcome.alpha)} · 측정 종료 ${data.outcome.measurement_end_date}`
        : "성과 측정 윈도우가 끝나면 outcome을 생성해야 한다.",
    },
    {
      label: "주문 경계",
      value: "자동 주문 없음",
      detail: "이 판정은 추천 품질 검토이며 브로커 주문 흐름을 실행하지 않는다.",
    },
  ];
}

function traceStatusLabel(status: string) {
  if (status === "linked" || status === "review_linked") {
    return "연결됨";
  }
  if (status === "position_without_review") {
    return "보유만 확인";
  }
  if (status === "not_in_portfolio") {
    return "미보유";
  }
  if (status === "missing") {
    return "직접 근거 없음";
  }
  return koCode(status);
}

function evidenceTraceCards(data: RecommendationDetailData) {
  const trace = data.evidence_trace;
  const direct = trace.direct_news_or_ai;
  const macroFlow = trace.macro_flow;
  const holding = trace.holding_review;
  const directHref = direct.evidence_id ? evidenceHref(direct.evidence_id, data.symbol) : null;
  const holdingHref = portfolioCoverageHref(holding.review_date);
  const firstFlow = macroFlow.recent_flows[0];

  return [
    {
      label: "뉴스/AI 분석",
      value: traceStatusLabel(direct.status),
      detail:
        direct.status === "linked"
          ? `직접 종목 뉴스나 AI 근거가 추천 입력으로 연결됐다. 신뢰도 ${formatMetricValue(direct.confidence)}.`
          : "이 추천은 직접 종목 뉴스보다 가격, 유니버스, 또는 상위 흐름 근거가 중심이다.",
      href: directHref,
      hrefLabel: direct.evidence_id ? evidenceLinkLabel(direct.evidence_id) : null,
      newsTitle:
        direct.title && direct.status === "linked"
          ? {
              title: direct.title,
              symbol: data.symbol,
              impactDirection: direct.impact_direction,
              impactScore: direct.impact_strength,
            }
          : null,
    },
    {
      label: "상위 흐름 전파",
      value: macroFlow.propagated_impact_count > 0 ? `${macroFlow.propagated_impact_count}개 반영` : "반영 없음",
      detail:
        macroFlow.propagated_impact_count > 0
          ? `${firstFlow ? `${koCode(firstFlow.theme_key)} 흐름` : "시장/테마 흐름"}이 종목 노출도 규칙을 거쳐 점수 입력으로 들어갔다.`
          : "거시·테마 뉴스가 이 종목 점수로 전파된 기록은 아직 없다.",
      href: `/stocks/${encodeURIComponent(data.symbol)}` as Route,
      hrefLabel: "종목 흐름 보기",
      newsTitle:
        firstFlow && macroFlow.propagated_impact_count > 0
          ? {
              title: firstFlow.title,
              symbol: data.symbol,
              themeKey: firstFlow.theme_key,
              impactDirection: firstFlow.impact_direction,
              impactScore: firstFlow.impact_strength,
            }
          : null,
    },
    {
      label: "보유검토 연결",
      value: traceStatusLabel(holding.status),
      detail:
        holding.status === "review_linked"
          ? `${koCode(holding.action)} · ${holding.reason ?? "보유검토 항목과 연결됨"}`
          : holding.status === "position_without_review"
            ? `포지션 ${formatMetricValue(holding.current_weight)}가 있으나 최신 보유검토 항목은 아직 연결되지 않았다.`
            : "현재 포트폴리오 보유 항목으로 확인되지 않았다.",
      href: holdingHref,
      hrefLabel: "보유 검토 보기",
      newsTitle: null,
    },
  ];
}

export default async function RecommendationPage({ params }: RecommendationPageProps) {
  const { recommendationId } = await params;
  const response = await getRecommendationDetail(recommendationId);
  const data = response.data;
  const evidenceReview = data.evidence_review;
  const qualityDecision = recommendationQualityDecision(data);
  const qualityChecks = recommendationQualityChecks(data);
  const traceCards = evidenceTraceCards(data);
  const macroFlowComponents = data.score_components.filter((component) => macroFlowRows(component).length > 0);
  const outcomeMeasured = data.outcome.label !== "unmeasured" && Boolean(data.outcome.measurement_end_date);
  const marketComponentCount = data.score_components.filter((component) =>
    ["market_feature", "strategy_universe_rank"].includes(component.provenance?.source_type ?? ""),
  ).length;
  const aiOrEventComponentCount = data.score_components.filter(
    (component) => component.provenance?.source_type === "event_or_ai_evidence",
  ).length;
  const recommendationReadingCards = [
    {
      label: "결론",
      title: `${koCode(data.recommendation)} · ${formatPercent(data.score)}`,
      body: "이 값은 자동 주문이 아니라 사람 검토를 시작할지 정하는 읽기 전용 점수다.",
    },
    {
      label: "가격/순위",
      title: `${marketComponentCount}개 재료`,
      body: "가격 흐름, 수집 기간, 전략 유니버스 순위처럼 숫자로 검증 가능한 입력이다.",
    },
    {
      label: "뉴스/AI",
      title: `${aiOrEventComponentCount}개 재료`,
      body: "회사나 종목을 직접 언급한 뉴스, 공시, AI 구조화 결과가 붙은 경우다.",
    },
    {
      label: "상위 흐름",
      title: `${macroFlowComponents.length}개 재료`,
      body: "종목을 직접 언급하지 않은 시장·테마 뉴스가 노출도 규칙으로 점수에 들어간 경우다.",
    },
  ];

  return (
    <div className="pageStack">
      <section className="reveal">
        <div className="bento-badge">
          추천 • {koCode(data.strategy_name)} • {koCode(data.horizon_type)} • {data.as_of_date}
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "24px", flexWrap: "wrap" }}>
          <div>
            <h1 style={{ fontSize: "clamp(2.5rem, 4vw, 4rem)", marginBottom: "16px" }}>{data.symbol} 추천 검토서</h1>
            <p style={{ color: "var(--text-secondary)", fontSize: "1.1rem", maxWidth: "700px" }}>
              추천은 자동 매매 명령이 아니라 점수, 증거, 측정된 성과를 함께 검토하는 입력값이다.
              포트폴리오 조치 전 연결된 투자 논리와 성과를 함께 확인한다.
            </p>
          </div>
          
          <div style={{ 
            padding: "20px 32px", 
            background: "rgba(59, 130, 246, 0.1)", 
            border: "1px solid rgba(59, 130, 246, 0.2)",
            borderRadius: "var(--radius-md)",
            textAlign: "center"
          }}>
            <span className="metric-sub" style={{ color: "var(--accent-blue)" }}>종합 점수</span>
            <div style={{ fontSize: "2.5rem", fontWeight: 700, color: "var(--text-primary)", margin: "4px 0" }}>
              {formatPercent(data.score)}
            </div>
            <div style={{ fontSize: "0.85rem", color: "var(--accent-blue)", fontWeight: 700 }}>
              {koCode(data.recommendation)}
            </div>
          </div>
        </div>
      </section>

      <section className="bento-card reveal delay-1" aria-label="중장기 추천 품질 판정">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "20px", flexWrap: "wrap", marginBottom: "20px" }}>
          <div>
            <span className="metric-sub">중장기 품질 판정</span>
            <h2 style={{ fontSize: "1.5rem", marginTop: "6px" }}>{qualityDecision.status}</h2>
            <p style={{ color: "var(--text-secondary)", marginTop: "8px", maxWidth: "820px" }}>
              {qualityDecision.summary}
            </p>
          </div>
          <span className={`risk-tag ${qualityDecision.tone}`}>읽기 전용 평가</span>
        </div>
        <div className="flow-steps">
          {qualityChecks.map((check) => (
            <article className="flow-step" key={check.label}>
              <span>{check.label}</span>
              <strong>{check.value}</strong>
              <p>{check.detail}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="detail-path-grid reveal delay-1" aria-label="추천 상세 읽는 순서">
        {recommendationReadingCards.map((card) => (
          <article className="detail-path-card" key={card.label}>
            <span>{card.label}</span>
            <strong>{card.title}</strong>
            <p>{card.body}</p>
          </article>
        ))}
      </section>

      <section className="bento-card reveal delay-1" aria-label="추천 근거 흐름 요약">
        <div style={{ marginBottom: "20px" }}>
          <span className="metric-sub">근거 흐름 요약</span>
          <h2 style={{ fontSize: "1.5rem", marginTop: "6px" }}>무엇을 보고 이 추천을 검토해야 하나</h2>
          <p style={{ color: "var(--text-secondary)", marginTop: "8px", maxWidth: "820px" }}>
            뉴스와 AI 구조화 결과는 바로 주문으로 이어지지 않는다. 직접 종목 뉴스, 시장·테마 흐름, 보유검토 상태를
            분리해서 확인한 뒤 사람 검토에서 채택 여부를 결정한다.
          </p>
        </div>

        <div className="flow-steps">
          {traceCards.map((card) => (
            <article className="flow-step" key={card.label}>
              <span>{card.label}</span>
              <strong>{card.value}</strong>
              <p>{card.detail}</p>
              {card.newsTitle ? <NewsTitleBlock compact {...card.newsTitle} /> : null}
              {card.href && card.hrefLabel ? <Link href={card.href}>{card.hrefLabel}</Link> : null}
            </article>
          ))}
        </div>
      </section>

      {macroFlowComponents.length > 0 ? (
        <section className="bento-card reveal delay-1" aria-label="상위 흐름 전파 경로">
          <div style={{ marginBottom: "22px" }}>
            <span className="metric-sub">상위 흐름 전파 경로</span>
            <h2 style={{ fontSize: "1.5rem", marginTop: "6px" }}>시장·테마 뉴스가 {data.symbol} 점수에 들어간 방식</h2>
            <p style={{ color: "var(--text-secondary)", marginTop: "8px", maxWidth: "820px" }}>
              이 패널은 종목을 직접 언급하지 않은 뉴스가 테마와 종목 노출도 규칙을 거쳐 추천 점수에 들어간 경로다.
              전체 전파 근거 수와 아래에 표시된 최근 사례 수는 다를 수 있다. AI가 주문을 결정한 것이 아니라,
              구조화된 흐름이 점수 입력으로만 쓰였다.
            </p>
          </div>

          <div className="bento-list">
            {macroFlowComponents.map((component) => {
              const rows = macroFlowRows(component);
              return (
                <div className="bento-list-item" key={component.component} style={{ alignItems: "flex-start", flexDirection: "column" }}>
                  <div style={{ width: "100%", display: "flex", justifyContent: "space-between", gap: "16px", flexWrap: "wrap" }}>
                    <div>
                      <span className="metric-sub">{koCode(component.component)}</span>
                      <strong>{formatPercent(component.value)} · 가중치 {formatPercent(component.weight)}</strong>
                    </div>
                    <span style={{ color: "var(--text-secondary)" }}>
                      전체 전파 근거 {component.provenance?.evidence?.propagated_impact_count ?? rows.length}개 · 최근 표시 {rows.length}개
                    </span>
                  </div>

                  <div className="relationship-list" aria-label={`${data.symbol} 상위 흐름 전파 근거`}>
                    {rows.map((flow) => {
                      const href = themeHref(flow.theme_key);
                      return (
                        <div className="relationship-chip" key={`${component.component}-${flow.event_id}-${flow.theme_key}`}>
                          <span>{koCode(flow.theme_key)}</span>
                          <NewsTitleBlock
                            compact
                            title={flow.title}
                            symbol={data.symbol}
                            themeKey={flow.theme_key}
                            impactDirection={flow.impact_direction}
                            impactScore={flow.impact_strength}
                          />
                          <small>
                            {koCode(flow.impact_direction)} · 강도 {formatMetricValue(flow.impact_strength)} · 신뢰도 {formatMetricValue(flow.confidence)}
                          </small>
                          <small>
                            노출도 {formatMetricValue(flow.exposure_weight)} · 발생 {flow.event_at}
                          </small>
                          {href ? <Link href={href}>테마 흐름 보기</Link> : null}
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      ) : null}

      <section className="bento-card reveal delay-1" aria-label="추천 근거 품질 점검">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "20px", flexWrap: "wrap", marginBottom: "20px" }}>
          <div>
            <span className="metric-sub">근거 품질 점검</span>
            <h2 style={{ fontSize: "1.5rem", marginTop: "6px" }}>{koCode(evidenceReview.quality_status)}</h2>
            <p style={{ color: "var(--text-secondary)", marginTop: "8px", maxWidth: "760px" }}>
              이 점검은 추천 점수를 새로 만들지 않는다. 추천이 투자 논리, 점수 구성요소, AI/이벤트 근거, 성과 측정과
              충분히 연결됐는지 확인하는 읽기 전용 검토다.
            </p>
          </div>
          <div className="status-rail compact-rail" style={{ flex: "1 1 360px" }}>
            <div className="rail-cell">
              <span>통과</span>
              <strong>{reviewCount(evidenceReview.summary.pass_count)}</strong>
              <small>검토 기준 충족</small>
            </div>
            <div className="rail-cell">
              <span>주의</span>
              <strong>{reviewCount(evidenceReview.summary.warning_count)}</strong>
              <small>보강 필요</small>
            </div>
            <div className="rail-cell">
              <span>차단</span>
              <strong>{reviewCount(evidenceReview.summary.blocked_count)}</strong>
              <small>진행 금지</small>
            </div>
          </div>
        </div>

        <div className="bento-list">
          {evidenceReview.gates.map((gate) => (
            <div className="bento-list-item" key={gate.gate_key}>
              <div>
                <span className="metric-sub" style={{ color: gateStatusColor(gate.status) }}>{gateStatusLabel(gate.status)}</span>
                <strong>{koLabel(gate.label)}</strong>
                <span>{koLabel(gate.detail)}</span>
              </div>
              <span style={{ color: "var(--text-secondary)", maxWidth: "360px" }}>{koLabel(gate.next_step)}</span>
            </div>
          ))}
        </div>
      </section>

      <section className="bento-grid reveal delay-1">
        <article className="bento-card span-2">
          <div style={{ marginBottom: "24px" }}>
            <span className="metric-sub">점수 근거</span>
            <h2 style={{ fontSize: "1.5rem" }}>{koCode(data.score_version)}</h2>
          </div>
          
          <div className="bento-list">
            {data.score_components.map((component) => {
              const href = evidenceHref(component.evidence_id, data.symbol);
              const badges = provenanceBadges(component);
              return (
                <div className="bento-list-item" key={component.component} style={{ alignItems: "flex-start", gap: "18px" }}>
                  <div style={{ flex: "1 1 360px", minWidth: 0 }}>
                    <strong style={{ display: "block", marginBottom: "6px" }}>{koCode(component.component)}</strong>
                    <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem", lineHeight: 1.55, margin: "0 0 10px" }}>
                      {provenanceDetail(component)}
                    </p>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: "8px", marginBottom: "10px" }}>
                      {badges.map((badge) => (
                        <span key={`${component.component}-${badge}`} style={{
                          border: "1px solid var(--border-light)",
                          borderRadius: "999px",
                          color: "var(--text-secondary)",
                          fontSize: "0.72rem",
                          padding: "4px 8px"
                        }}>
                          {badge}
                        </span>
                      ))}
                    </div>
                    <div className="mini-link-stack">
                      {href ? (
                        <Link href={href}>
                          {evidenceLinkLabel(component.evidence_id)}
                        </Link>
                      ) : (
                        <span>상세 추적은 아래 ID에서 확인</span>
                      )}
                    </div>
                    <AuditMetadata items={provenanceMetadata(component)} summary="추적 ID 보기" />
                  </div>
                  <div style={{ flex: "0 0 110px", textAlign: "right" }}>
                    <strong style={{ fontSize: "1.1rem", color: "var(--text-primary)" }}>{formatPercent(component.value)}</strong>
                  </div>
                  <div style={{ flex: "0 0 120px", textAlign: "right" }}>
                    <span className="metric-sub">가중치 {formatPercent(component.weight)}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </article>

        <article className="bento-card span-2">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: "24px" }}>
            <div>
              <span className="metric-sub">성과 측정</span>
              <h2 style={{ fontSize: "1.5rem" }}>
                {outcomeMeasured ? koCode(data.outcome.label) : "아직 성과 측정 전"}
              </h2>
            </div>
            <Link className="btn btn-primary" href={`/theses/${data.linked_thesis_id}`}>
              연결된 투자 논리 열기
            </Link>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
            <div style={{ padding: "16px", background: "rgba(255,255,255,0.03)", border: "1px solid var(--border-light)", borderRadius: "var(--radius-sm)" }}>
              <span className="metric-sub">알파</span>
              <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "var(--text-primary)" }}>
                {outcomeMeasured ? formatPercent(data.outcome.alpha) : "측정 전"}
              </div>
            </div>
            <div style={{ padding: "16px", background: "rgba(255,255,255,0.03)", border: "1px solid var(--border-light)", borderRadius: "var(--radius-sm)" }}>
              <span className="metric-sub">절대수익률</span>
              <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "var(--text-primary)" }}>
                {outcomeMeasured ? formatPercent(data.outcome.absolute_return) : "측정 전"}
              </div>
            </div>
            <div style={{ padding: "16px", background: "rgba(255,255,255,0.03)", border: "1px solid var(--border-light)", borderRadius: "var(--radius-sm)" }}>
              <span className="metric-sub">벤치마크 수익률</span>
              <div style={{ fontSize: "1.5rem", fontWeight: 700, color: "var(--text-primary)" }}>
                {outcomeMeasured ? formatPercent(data.outcome.benchmark_return) : "측정 전"}
              </div>
            </div>
            <div style={{ padding: "16px", background: "rgba(255,255,255,0.03)", border: "1px solid var(--border-light)", borderRadius: "var(--radius-sm)" }}>
              <span className="metric-sub">측정 종료일</span>
              <div style={{ fontSize: "1.1rem", fontWeight: 600, color: "var(--text-primary)", marginTop: "4px" }}>
                {outcomeMeasured ? data.outcome.measurement_end_date : "성과 측정 윈도우 대기"}
              </div>
            </div>
          </div>
        </article>
      </section>
    </div>
  );
}
