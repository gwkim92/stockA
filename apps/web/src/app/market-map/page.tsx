import Link from "next/link";
import type { Route } from "next";

import { getMarketMap } from "@/lib/frontend-api";
import { koCode } from "@/lib/korean-labels";
import type { MarketMapData } from "@/lib/types";

export const dynamic = "force-dynamic";
export const metadata = { title: "시장 지도" };

type MarketGroup = MarketMapData["groups"][number];
type MarketIndicator = MarketGroup["indicators"][number];
type MarketCorrelation = MarketMapData["correlations"][number];
type MarketNewsLink = MarketMapData["news_links"][number];
type MarketQualityFlag = MarketMapData["quality_flags"][number];
type MarketRegime = MarketMapData["regimes"][number];

const VISIBLE_INDICATOR_COUNT = 3;
const VISIBLE_QUALITY_FLAG_COUNT = 5;
const VISIBLE_NEWS_LINK_GROUP_COUNT = 6;

function formatPercent(value: number | null | undefined) {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return "미측정";
  }
  return `${Math.round(value * 1000) / 10}%`;
}

function formatValue(value: number | null | undefined) {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return "미측정";
  }
  return new Intl.NumberFormat("ko-KR", { maximumFractionDigits: 2 }).format(value);
}

function formatCoefficient(value: number | null | undefined) {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return "미측정";
  }
  return new Intl.NumberFormat("ko-KR", {
    maximumFractionDigits: 2,
    minimumFractionDigits: 2,
    signDisplay: "exceptZero",
  }).format(value);
}

function freshnessLabel(status: string) {
  if (status === "fresh") {
    return "최신";
  }
  if (status === "stale") {
    return "오래됨";
  }
  if (status === "missing") {
    return "없음";
  }
  return koCode(status);
}

function correlationRelationshipLabel(label: string) {
  if (label === "strong_positive") {
    return "강한 동행";
  }
  if (label === "strong_negative") {
    return "강한 반대";
  }
  if (label === "moderate_positive") {
    return "보통 동행";
  }
  if (label === "moderate_negative") {
    return "보통 반대";
  }
  return "약하거나 불명확";
}

function correlationTone(correlation: MarketCorrelation) {
  if (correlation.relationship_label.includes("strong")) {
    return "detail-path-card is-watch";
  }
  if (correlation.relationship_label.includes("moderate")) {
    return "detail-path-card is-good";
  }
  return "detail-path-card";
}

function correlationSummaryText(data: MarketMapData) {
  if (data.summary.correlation_count <= 0) {
    return "아직 계산된 상관관계가 없다. 장마감 후 동조성 분석이 끝나면 이 영역에 표시한다.";
  }
  const strong = data.summary.strong_correlation_count;
  const moderate = data.summary.moderate_correlation_count;
  return `${data.summary.correlation_count}개 쌍 계산 · 강한 동조/반대 ${strong}개 · 보통 수준 ${moderate}개`;
}

function regimeTitle(regime: MarketRegime) {
  return koCode(regime.regime_code);
}

function regimeTone(regime: MarketRegime) {
  if (regime.regime_state === "active") {
    return "decision-card is-watch";
  }
  if (regime.regime_state === "watch") {
    return "decision-card is-good";
  }
  return "decision-card";
}

function indicatorTone(indicator: MarketIndicator) {
  if (indicator.freshness_status === "missing") {
    return "detail-path-card is-blocked";
  }
  if (indicator.freshness_status === "stale") {
    return "detail-path-card is-watch";
  }
  if (indicator.shock_direction !== "neutral") {
    return "detail-path-card is-good";
  }
  return "detail-path-card";
}

function indicatorPressureLabel(indicator: MarketIndicator) {
  if (indicator.freshness_status === "missing") {
    return "판단 제외";
  }
  if (indicator.freshness_status === "stale") {
    return "신뢰도 낮춤";
  }
  if (indicator.shock_direction === "up") {
    return "상승 압력";
  }
  if (indicator.shock_direction === "down") {
    return "하락 압력";
  }
  return "중립";
}

function indicatorSortScore(indicator: MarketIndicator) {
  const qualityPenalty = indicator.freshness_status === "missing" ? 100 : indicator.freshness_status === "stale" ? 80 : 0;
  const shockScore = indicator.shock_direction === "neutral" ? 0 : 40;
  return qualityPenalty + shockScore + Math.round((indicator.shock_magnitude || 0) * 100);
}

function rankedIndicators(group: MarketGroup) {
  return [...group.indicators].sort((left, right) => indicatorSortScore(right) - indicatorSortScore(left));
}

function strongestIndicator(group: MarketGroup) {
  return (
    group.indicators.find((indicator) => indicator.indicator_code === group.strongest_indicator_code) ||
    rankedIndicators(group)[0] ||
    null
  );
}

function groupSummary(group: MarketGroup) {
  const strongest = strongestIndicator(group);
  const quality =
    group.missing_count > 0
      ? `${group.missing_count}개 지표가 비어 있다`
      : group.stale_count > 0
        ? `${group.stale_count}개 지표가 오래됐다`
        : "지표가 정상 관측 중이다";
  const shock = group.shock_count > 0 ? `움직임 큰 지표 ${group.shock_count}개` : "큰 가격 충격은 없다";
  return `${quality}. ${shock}. 가장 먼저 볼 지표는 ${strongest?.display_name || "아직 없음"}이다.`;
}

function groupTone(group: MarketGroup) {
  if (group.missing_count > 0) {
    return "market-pressure-card is-block";
  }
  if (group.stale_count > 0) {
    return "market-pressure-card is-watch";
  }
  if (group.shock_count > 0) {
    return "market-pressure-card is-hot";
  }
  return "market-pressure-card";
}

function qualityCardText(data: MarketMapData) {
  const qualityIssueCount = data.summary.stale_indicator_count + data.summary.missing_indicator_count;
  if (qualityIssueCount > 0) {
    return `${qualityIssueCount}개 지표는 추정하지 않는다. 오래됐거나 비어 있는 값은 판단에서 낮춰 본다.`;
  }
  return "시장 지표와 시장 체제 계산이 준비됐다. 추천 비중은 성과 검증 전까지 바꾸지 않는다.";
}

function sourcePolicyText(indicator: MarketIndicator) {
  if (indicator.indicator_code === "XAG_USD") {
    return "은 현물 가격이 아니라 FRED 프록시 지수다. 방향성 보조 지표로만 쓴다.";
  }
  if (indicator.preferred_provider === "fred") {
    return "FRED 공식 원천을 가공 지표로만 표시한다. 지연값은 추정하지 않는다.";
  }
  if (indicator.preferred_provider === "twelve_data") {
    return "Twelve Data 무료 한도 안에서 가공 지표만 표시한다. 원시 데이터 재배포는 하지 않는다.";
  }
  if (indicator.preferred_provider === "cboe_csv") {
    return "CBOE 공개 파일을 정규화해 표시한다. 원본 파일을 그대로 재배포하지 않는다.";
  }
  return "원천 표기와 가공 지표만 사용한다. 인과를 단정하지 않는다.";
}

function normalizeOperationalText(text: string | null | undefined) {
  return (text || "추가 조치 없음")
    .replaceAll("provider fetch와", "원천 수집과")
    .replaceAll("stale", "오래된")
    .replaceAll("provider fetch", "원천 수집")
    .replaceAll("snapshot", "시장 스냅샷")
    .replaceAll("rerun", "재실행")
    .replaceAll("오래된이다", "오래된 상태다")
    .replaceAll("regime", "체제")
    .replaceAll("체제이", "체제가")
    .replaceAll("weight", "가중치")
    .replaceAll("outcome", "성과");
}

function marketRelationshipLabel(relationship: string | null | undefined) {
  const raw = relationship || "";
  if (raw.includes("news") && raw.includes("indicator")) {
    return "뉴스-지표 동시 관찰";
  }
  return normalizeOperationalText(koCode(raw) || "동시 관찰");
}

function humanizeNewsRationale(rationale: string) {
  return normalizeOperationalText(rationale)
    .replaceAll("QUANTUM_COMPUTING_POLICY", koCode("QUANTUM_COMPUTING_POLICY"))
    .replaceAll("AI_SEMICONDUCTOR_CYCLE", koCode("AI_SEMICONDUCTOR_CYCLE"))
    .replaceAll("TECH_DOMAIN", koCode("TECH_DOMAIN"))
    .replaceAll("ENERGY_GEOPOLITICS", koCode("ENERGY_GEOPOLITICS"))
    .replaceAll("MACRO_RATES_FED", koCode("MACRO_RATES_FED"))
    .replaceAll("shock", "가격 충격")
    .replaceAll("사이클와", "사이클과")
    .replaceAll("도메인와", "도메인과");
}

function activeRegimeText(regimes: MarketRegime[]) {
  if (regimes.length === 0) {
    return "켜진 체제 없음";
  }
  return regimes.map(regimeTitle).join(", ");
}

function groupNewsLinks(links: MarketNewsLink[]) {
  const groups = new Map<
    string,
    {
      indicator_code: string;
      indicator_name: string;
      links: MarketNewsLink[];
      confidence_total: number;
      relationships: Set<string>;
      sources: Set<string>;
      rationales: Set<string>;
    }
  >();

  for (const link of links) {
    const key = link.indicator_code || link.indicator_name || "unknown_indicator";
    const current =
      groups.get(key) ||
      {
        indicator_code: link.indicator_code,
        indicator_name: link.indicator_name || link.indicator_code,
        links: [],
        confidence_total: 0,
        relationships: new Set<string>(),
        sources: new Set<string>(),
        rationales: new Set<string>(),
      };
    current.links.push(link);
    current.confidence_total += link.confidence || 0;
    if (link.relationship) {
      current.relationships.add(marketRelationshipLabel(link.relationship));
    }
    if (link.source_name) {
      current.sources.add(link.source_name);
    }
    if (link.rationale) {
      current.rationales.add(humanizeNewsRationale(link.rationale));
    }
    groups.set(key, current);
  }

  return [...groups.values()]
    .map((group) => ({
      ...group,
      average_confidence: group.links.length > 0 ? group.confidence_total / group.links.length : 0,
      top_titles: group.links
        .map((link) => link.title_ko || "제목 미수집")
        .filter((title, index, titles) => titles.indexOf(title) === index)
        .slice(0, 4),
      relationship_label: [...group.relationships].join(", ") || "동시 관찰",
      source_label: [...group.sources].slice(0, 3).join(", ") || "원천 미표기",
      rationale_label: [...group.rationales].slice(0, 2).join(" / ") || "가격 충격과 뉴스가 같은 기간에 관찰됐다.",
    }))
    .sort((left, right) => right.links.length - left.links.length || right.average_confidence - left.average_confidence);
}

function qualityFlagSummary(flags: MarketQualityFlag[]) {
  const staleCount = flags.filter((flag) => flag.freshness_status === "stale").length;
  const missingCount = flags.filter((flag) => flag.freshness_status === "missing").length;
  if (missingCount > 0) {
    return `비어 있는 지표 ${missingCount}개와 오래된 지표 ${staleCount}개가 있다. 해당 지표는 추정하지 않고 판단 신뢰도를 낮춘다.`;
  }
  if (staleCount > 0) {
    return `오래된 지표 ${staleCount}개가 있다. 최신 수집이 확인될 때까지 체제 판단의 보조 근거로만 쓴다.`;
  }
  return "시장 지표 품질 플래그가 없다. 그래도 추천 산식 반영 비중과 주문은 자동 변경하지 않는다.";
}

function buildMarketReadout(data: MarketMapData, regimes: MarketRegime[]) {
  const qualityIssueCount = data.summary.stale_indicator_count + data.summary.missing_indicator_count;
  const activeCount = data.summary.active_regime_count;
  const watchCount = data.summary.watch_regime_count;
  const regimeNames = regimes.map(regimeTitle).join(", ");

  if (qualityIssueCount > 0) {
    return {
      tone: "is-watch",
      title: "오래된 지표는 낮춰 본다.",
      copy: `${qualityIssueCount}개 지표가 오래됐거나 비어 있다. 시장 판단은 가능하지만 해당 지표는 추정하지 않고 신뢰도를 낮춘다.`,
      nextSteps: ["오래된 지표 분리", "추정값 사용 금지", "수집 재실행 후 재판단"],
    };
  }

  if (activeCount > 0) {
    return {
      tone: "is-watch",
      title: "시장 체제 신호가 켜져 있다.",
      copy: `${regimeNames || "상위 체제"} 신호가 활성이다. 추천을 바로 바꾸지 말고 사이클 지도와 종목 노출도를 이어서 본다.`,
      nextSteps: ["활성 시장 체제 확인", "영향받는 테마 확인", "추천·보유 근거와 충돌 확인"],
    };
  }

  if (watchCount > 0 || data.summary.shock_indicator_count > 0) {
    return {
      tone: "is-good",
      title: "가격 충격은 있지만 체제 전환은 관찰 단계다.",
      copy: `${data.summary.shock_indicator_count}개 지표가 크게 움직였고 ${watchCount}개 시장 체제를 감시 중이다. 아직 추천 점수는 바꾸지 않고 뉴스·사이클 근거와 대조한다.`,
      nextSteps: ["압력이 큰 영역 확인", "뉴스 연결 확인", "흐름 지도에서 전파 경로 확인"],
    };
  }

  return {
    tone: "is-good",
    title: "시장 배경은 판단 가능한 상태다.",
    copy: "수집 품질이 안정적이고 강한 체제 신호는 없다. 종목별 뉴스·사이클·재무 근거를 중심으로 추천 후보를 본다.",
    nextSteps: ["종목별 직접 근거 확인", "상위 흐름 전파 확인", "추천 상세에서 리스크 확인"],
  };
}

export default async function MarketMapPage() {
  const response = await getMarketMap();
  const data = response.data;
  const topRegimes = data.regimes.filter((regime) => ["active", "watch"].includes(regime.regime_state)).slice(0, 4);
  const topFlags = data.quality_flags.slice(0, VISIBLE_QUALITY_FLAG_COUNT);
  const hiddenFlags = data.quality_flags.slice(VISIBLE_QUALITY_FLAG_COUNT);
  const readout = buildMarketReadout(data, topRegimes);
  const pressureGroups = [...data.groups]
    .sort(
      (left, right) =>
        right.shock_count - left.shock_count ||
        right.stale_count + right.missing_count - (left.stale_count + left.missing_count),
    )
    .slice(0, 6);
  const newsLinkGroups = groupNewsLinks(data.news_links);
  const visibleNewsLinkGroups = newsLinkGroups.slice(0, VISIBLE_NEWS_LINK_GROUP_COUNT);
  const hiddenNewsLinkGroupCount = Math.max(0, newsLinkGroups.length - VISIBLE_NEWS_LINK_GROUP_COUNT);
  const topCorrelations = data.correlations.slice(0, 8);
  return (
    <div className="terminal-page decision-page market-map-page research-command-page">
      <section className="decision-brief workspace-brief reveal research-command-deck market-command-deck" aria-labelledby="market-map-title">
        <div className="decision-brief-main">
          <span className="decision-brief-kicker">시장 지도 · {data.snapshot_as_of_date || data.as_of_date}</span>
          <h1 className="decision-brief-title" id="market-map-title">
            {readout.title}
          </h1>
          <p className="decision-brief-copy">
            {readout.copy}
          </p>
          <div className="decision-brief-meta" aria-label="시장 지도 핵심 상태">
            <span>지표 {data.summary.indicator_count.toLocaleString("ko-KR")}개</span>
            <span>충격 {data.summary.shock_indicator_count.toLocaleString("ko-KR")}개</span>
            <span>활성 체제 {data.summary.active_regime_count.toLocaleString("ko-KR")}개</span>
            <span>뉴스 연결 {data.summary.news_link_count.toLocaleString("ko-KR")}개</span>
            <span>상관관계 {data.summary.correlation_count.toLocaleString("ko-KR")}개</span>
          </div>
        </div>
        <div className="decision-brief-grid workspace-command-grid">
          <a className={data.summary.stale_indicator_count + data.summary.missing_indicator_count > 0 ? "decision-card is-watch" : "decision-card is-good"} href="#market-quality">
            <span>먼저 볼 것</span>
            <strong>
              {data.summary.fresh_indicator_count.toLocaleString("ko-KR")}개 최신 ·{" "}
              {(data.summary.stale_indicator_count + data.summary.missing_indicator_count).toLocaleString("ko-KR")}개 낮춤
            </strong>
            <small>{qualityCardText(data)}</small>
            <b>품질 보기</b>
          </a>
          <a className="decision-card is-good" href="#market-pressure">
            <span>시장 압력</span>
            <strong>{data.summary.shock_indicator_count.toLocaleString("ko-KR")}개 지표 변동</strong>
            <small>가장 많이 움직인 영역부터 보고, 필요한 지표만 펼친다.</small>
            <b>압력 보기</b>
          </a>
          <a className={topRegimes.length > 0 ? "decision-card is-watch" : "decision-card"} href="#market-regimes">
            <span>상위 체제</span>
            <strong>{topRegimes.length.toLocaleString("ko-KR")}개 주시</strong>
            <small>위험자산 선호, 실질금리, 달러 유동성, 에너지 충격 같은 상위 조건이다.</small>
            <b>체제 보기</b>
          </a>
          <a className={data.summary.correlation_count > 0 ? "decision-card is-good" : "decision-card is-watch"} href="#market-correlations">
            <span>동조성</span>
            <strong>{data.summary.correlation_count.toLocaleString("ko-KR")}개 쌍 계산</strong>
            <small>종목이 지수·금리·달러·원자재와 최근 같이 움직였는지 본다. 원인 단정은 하지 않는다.</small>
            <b>동조성 보기</b>
          </a>
          <Link className="decision-card" href={"/cycle-map" as Route}>
            <span>사이클 연결</span>
            <strong>시장 → 흐름</strong>
            <small>시장 지표 압력이 거시·테마·종목 사이클로 어떻게 내려가는지 이어서 본다.</small>
            <b>흐름 지도</b>
          </Link>
        </div>
      </section>

      <section className="bento-card reveal delay-1" id="market-correlations" aria-label="상관관계 분석">
        <div className="section-heading stacked-heading">
          <span>상관관계</span>
          <h2>종목이 무엇과 같이 움직였는지 본다</h2>
          <p>
            {correlationSummaryText(data)}. 이 값은 최근 수익률 동조성이다. 뉴스 원인이나 매수·매도 이유를 단정하지 않고,
            포트폴리오 집중과 추천 리스크를 점검하는 입력으로만 쓴다.
          </p>
        </div>
        {topCorrelations.length > 0 ? (
          <div className="detail-path-grid">
            {topCorrelations.map((correlation) => (
              <article
                className={correlationTone(correlation)}
                key={`${correlation.primary_asset_key}-${correlation.comparison_asset_key}-${correlation.lookback_days}`}
              >
                <span>
                  {correlationRelationshipLabel(correlation.relationship_label)} · {correlation.lookback_days}일 · 신뢰도{" "}
                  {formatPercent(correlation.confidence)}
                </span>
                <strong>
                  {correlation.primary_display_name} ↔ {correlation.comparison_display_name}
                </strong>
                <small>
                  상관계수 {formatCoefficient(correlation.correlation)} · 베타 {formatCoefficient(correlation.beta)} · 관측{" "}
                  {correlation.observation_count.toLocaleString("ko-KR")}개
                </small>
                <p>{correlation.summary_ko}</p>
              </article>
            ))}
          </div>
        ) : (
          <div className="empty-state compact">
            <strong>상관관계가 아직 계산되지 않았다.</strong>
            <span>장마감 후 상관관계 분석이 실행되면 종목과 시장 지표의 동조성이 여기에 표시된다.</span>
          </div>
        )}
      </section>

      <section className="bento-card reveal delay-2" id="market-pressure" aria-label="시장 압력판">
        <div className="section-heading stacked-heading">
          <span>압력판</span>
          <h2>지금 가장 먼저 볼 시장 영역</h2>
          <p>충격이 큰 영역부터 보여준다. 정상 영역도 숨기지 않지만, 처음 판단은 큰 변화와 품질 이슈에서 시작한다.</p>
        </div>
        <div className="market-pressure-grid">
          {pressureGroups.map((group) => {
            const strongest = strongestIndicator(group);
            return (
              <a className={groupTone(group)} href={`#group-${group.group_code}`} key={group.group_code}>
                <span>{group.group_name}</span>
                <strong>{strongest?.display_name || "대표 지표 없음"}</strong>
                <small>{groupSummary(group)}</small>
                <b>
                  충격 {group.shock_count} · 품질 이슈 {group.stale_count + group.missing_count}
                </b>
              </a>
            );
          })}
        </div>
      </section>

      <section className="bento-card reveal delay-3" id="market-regimes" aria-label="시장 체제 신호">
        <div className="section-heading stacked-heading">
          <span>먼저 볼 상위 조건</span>
          <h2>현재 켜져 있거나 감시 중인 시장 체제</h2>
          <p>이 신호는 주문을 만들지 않는다. 종목 추천과 보유 검토의 배경 조건으로만 쓴다.</p>
        </div>
        {topRegimes.length > 0 ? (
          <div className="decision-brief-grid">
            {topRegimes.map((regime) => (
              <article className={regimeTone(regime)} id={`regime-${regime.regime_code}`} key={regime.regime_code}>
                <span>{koCode(regime.regime_state)} · 신뢰도 {formatPercent(regime.confidence)}</span>
                <strong>{regimeTitle(regime)}</strong>
                <small>{regime.summary_ko}</small>
                <b>점수 {formatPercent(regime.regime_score)}</b>
              </article>
            ))}
          </div>
        ) : (
          <div className="empty-state">활성 또는 감시 중인 시장 체제가 아직 없다. 시장 지표 수집을 먼저 확인한다.</div>
        )}
      </section>

      <section className="reveal delay-4" id="market-groups" aria-label="시장 지표 묶음">
        <div className="market-group-stack">
          {data.groups.length === 0 ? (
            <article className="empty-state">
              표시할 시장 지표가 없다. 시장 지표 수집과 시장 체제 계산을 실행한 뒤 다시 확인한다.
            </article>
          ) : null}
          {data.groups.map((group) => {
            const ranked = rankedIndicators(group);
            const visible = ranked.slice(0, VISIBLE_INDICATOR_COUNT);
            const hidden = ranked.slice(VISIBLE_INDICATOR_COUNT);
            return (
              <section
                className="market-group-panel"
                id={`group-${group.group_code}`}
                key={group.group_code}
                aria-label={`${group.group_name} 시장 지표`}
              >
                <div className="market-group-header">
                  <div>
                    <span className="metric-sub">{group.group_name}</span>
                    <h2>{group.group_name} 흐름</h2>
                    <p>{groupSummary(group)}</p>
                  </div>
                  <span className="relation-pill">
                    최신 {group.fresh_count} · 오래됨 {group.stale_count} · 없음 {group.missing_count}
                  </span>
                </div>

                <div className="market-indicator-grid">
                  {visible.map((indicator) => (
                    <article className={indicatorTone(indicator)} id={`indicator-${indicator.indicator_code}`} key={indicator.indicator_code}>
                      <span>
                        {freshnessLabel(indicator.freshness_status)} · {indicatorPressureLabel(indicator)}
                      </span>
                      <strong>{indicator.display_name}</strong>
                      <p>{indicator.quality_note_ko || indicator.note_ko}</p>
                      <div className="market-indicator-metrics">
                        <small>값 {formatValue(indicator.latest_value)}</small>
                        <small>20일 {formatPercent(indicator.return_20d)}</small>
                        <small>충격 {formatPercent(indicator.shock_magnitude)}</small>
                        <small>신뢰 {formatPercent(indicator.confidence)}</small>
                      </div>
                      <details className="secondary-details market-source-details">
                        <summary>원천과 정책</summary>
                        <div className="relationship-list">
                          <div className="relationship-chip">
                            <span>{koCode(indicator.preferred_provider)}</span>
                            <strong>{indicator.provider_symbol || indicator.indicator_code}</strong>
                            <small>{sourcePolicyText(indicator)}</small>
                          </div>
                          <div className="relationship-chip">
                            <span>수집 정책</span>
                            <strong>{indicator.latest_observation_date || "관측일 없음"}</strong>
                            <small>인과 확정 아님 · 추천 비중 변경 없음</small>
                          </div>
                        </div>
                      </details>
                    </article>
                  ))}
                </div>

                {hidden.length > 0 ? (
                  <details className="market-hidden-indicators">
                    <summary>나머지 지표 {hidden.length.toLocaleString("ko-KR")}개 보기</summary>
                    <div className="market-compact-list">
                      {hidden.map((indicator) => (
                        <a href={`#indicator-${indicator.indicator_code}`} key={indicator.indicator_code}>
                          <span>{indicator.display_name}</span>
                          <strong>{indicatorPressureLabel(indicator)}</strong>
                          <small>
                            20일 {formatPercent(indicator.return_20d)} · 충격 {formatPercent(indicator.shock_magnitude)} · 관측일{" "}
                            {indicator.latest_observation_date || "없음"}
                          </small>
                        </a>
                      ))}
                    </div>
                  </details>
                ) : null}
              </section>
            );
          })}
        </div>
      </section>

      <section className="bento-card reveal delay-3" id="market-quality" aria-label="시장 지표 품질">
        <div className="section-heading stacked-heading">
          <span>품질 플래그</span>
          <h2>판단 전에 먼저 빼고 봐야 할 것</h2>
          <p>{qualityFlagSummary(data.quality_flags)}</p>
        </div>
        {topFlags.length > 0 ? (
          <>
            <div className="relationship-list">
              {topFlags.map((flag) => (
                <div className="relationship-chip" key={`${flag.flag_code}-${flag.indicator_code}`}>
                  <span>{koCode(flag.severity)} · {freshnessLabel(flag.freshness_status)}</span>
                  <strong>{flag.display_name}</strong>
                  <small>{normalizeOperationalText(flag.message_ko)}</small>
                </div>
              ))}
            </div>
            {hiddenFlags.length > 0 ? (
              <details className="market-hidden-indicators">
                <summary>나머지 품질 플래그 {hiddenFlags.length.toLocaleString("ko-KR")}개 보기</summary>
                <div className="market-compact-list">
                  {hiddenFlags.map((flag) => (
                    <div className="market-compact-row" key={`${flag.flag_code}-${flag.indicator_code}`}>
                      <span>{flag.display_name}</span>
                      <strong>{freshnessLabel(flag.freshness_status)}</strong>
                      <small>{normalizeOperationalText(flag.message_ko)}</small>
                    </div>
                  ))}
                </div>
              </details>
            ) : null}
          </>
        ) : (
          <div className="empty-state">현재 표시할 품질 플래그가 없다.</div>
        )}
      </section>

      <section className="bento-card reveal delay-4" aria-label="뉴스와 시장 지표 연결">
        <div className="section-heading stacked-heading">
          <span>뉴스 연결</span>
          <h2>뉴스와 가격 지표가 같은 시기에 움직였는가</h2>
          <p>
            원천 뉴스가 같은 지표에 반복 연결되면 한 묶음으로 요약한다. 아래 연결은 인과 확정이 아니라, 뉴스 해석과 가격 충격이
            같은 시간 창에 있었는지 보여주는 근거 후보다.
          </p>
        </div>
        {visibleNewsLinkGroups.length > 0 ? (
          <div className="market-news-grid">
            {visibleNewsLinkGroups.map((group) => (
              <article className="market-news-cluster" key={group.indicator_code}>
                <div className="market-news-cluster-head">
                  <span>{group.indicator_name}</span>
                  <strong>{group.links.length.toLocaleString("ko-KR")}건 연결</strong>
                  <small>평균 신뢰 {formatPercent(group.average_confidence)} · {group.relationship_label}</small>
                </div>
                <p>{group.rationale_label}</p>
                <div className="market-news-cluster-meta">
                  <span>원천 {group.source_label}</span>
                  <span>인과 확정 아님</span>
                  <span>추천 가중치 변경 없음</span>
                </div>
                <ul className="market-news-title-list" aria-label={`${group.indicator_name} 연결 대표 뉴스`}>
                  {group.top_titles.map((title) => (
                    <li key={title}>{title}</li>
                  ))}
                </ul>
                <details className="secondary-details market-source-details">
                  <summary>연결된 뉴스 전체 보기</summary>
                  <div className="market-compact-list">
                    {group.links.map((link) => (
                      <a
                        href={link.source_url || "#"}
                        key={`${link.document_id}-${link.indicator_code}-${link.link_date}`}
                        rel="noreferrer"
                        target={link.source_url ? "_blank" : undefined}
                      >
                        <span>{link.title_ko || "제목 미수집"}</span>
                        <strong>{formatPercent(link.confidence)}</strong>
                        <small>{humanizeNewsRationale(link.rationale)}</small>
                      </a>
                    ))}
                  </div>
                </details>
              </article>
            ))}
          </div>
        ) : (
          <div className="empty-state">최근 14일 기준으로 뉴스와 시장 지표 shock 연결이 아직 없다.</div>
        )}
        {hiddenNewsLinkGroupCount > 0 ? (
          <p className="market-muted-note">추가 지표 연결 {hiddenNewsLinkGroupCount.toLocaleString("ko-KR")}개는 낮은 우선순위로 접었다.</p>
        ) : null}
        <div className="btn-row" style={{ marginTop: "18px" }}>
          <Link className="btn btn-primary" href={"/intelligence" as Route}>
            뉴스 근거 보기
          </Link>
          <Link className="btn btn-secondary" href={"/data-health" as Route}>
            수집 상태 보기
          </Link>
        </div>
      </section>
    </div>
  );
}
