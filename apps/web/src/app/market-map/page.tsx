import Link from "next/link";
import type { Route } from "next";

import { getMarketMap } from "@/lib/frontend-api";
import { koCode } from "@/lib/korean-labels";
import type { MarketMapData } from "@/lib/types";

export const dynamic = "force-dynamic";
export const metadata = { title: "시장 지도" };

type MarketGroup = MarketMapData["groups"][number];
type MarketIndicator = MarketGroup["indicators"][number];
type MarketRegime = MarketMapData["regimes"][number];

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

function directionLabel(direction: string) {
  if (direction === "up") {
    return "상승 압력";
  }
  if (direction === "down") {
    return "하락 압력";
  }
  return "중립";
}

function regimeTitle(regime: MarketRegime) {
  return koCode(regime.regime_code).replaceAll("_", " ");
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

function groupSummary(group: MarketGroup) {
  const quality =
    group.missing_count > 0
      ? `${group.missing_count}개 지표가 비어 있다`
      : group.stale_count > 0
        ? `${group.stale_count}개 지표가 오래됐다`
        : "지표가 정상 관측 중이다";
  const shock = group.shock_count > 0 ? `움직임 큰 지표 ${group.shock_count}개` : "큰 가격 충격은 없다";
  return `${quality}. ${shock}. 대표 확인 대상은 ${group.strongest_indicator_code || "아직 없음"}이다.`;
}

export default async function MarketMapPage() {
  const response = await getMarketMap();
  const data = response.data;
  const topRegimes = data.regimes.filter((regime) => ["active", "watch"].includes(regime.regime_state)).slice(0, 4);
  const topFlags = data.quality_flags.slice(0, 4);

  return (
    <div className="terminal-page decision-page">
      <section className="decision-brief reveal" aria-labelledby="market-map-title">
        <div className="decision-brief-main">
          <span className="decision-brief-kicker">시장 지도 · {data.snapshot_as_of_date || data.as_of_date}</span>
          <h1 className="decision-brief-title" id="market-map-title">
            지수·금리·달러·원자재가 지금 만드는 압력
          </h1>
          <p className="decision-brief-copy">
            이 화면은 시장의 배경 조건을 먼저 본다. 뉴스와 가격 지표가 같은 방향을 가리키는지 확인하고, 종목·추천
            판단은 그 다음 단계에서 따로 검토한다.
          </p>
          <div className="decision-brief-meta" aria-label="시장 지도 핵심 상태">
            <span>지표 {data.summary.indicator_count.toLocaleString("ko-KR")}개</span>
            <span>충격 {data.summary.shock_indicator_count.toLocaleString("ko-KR")}개</span>
            <span>활성 regime {data.summary.active_regime_count.toLocaleString("ko-KR")}개</span>
            <span>뉴스 연결 {data.summary.news_link_count.toLocaleString("ko-KR")}개</span>
          </div>
        </div>
        <div className="decision-brief-grid">
          <a className={data.summary.stale_indicator_count + data.summary.missing_indicator_count > 0 ? "decision-card is-watch" : "decision-card is-good"} href="#market-quality">
            <span>데이터 품질</span>
            <strong>
              {data.summary.fresh_indicator_count.toLocaleString("ko-KR")}개 최신 ·{" "}
              {(data.summary.stale_indicator_count + data.summary.missing_indicator_count).toLocaleString("ko-KR")}개 확인
            </strong>
            <small>{data.summary.next_action}</small>
            <b>품질 확인</b>
          </a>
          <a className="decision-card is-good" href="#market-groups">
            <span>시장 묶음</span>
            <strong>{data.groups.length.toLocaleString("ko-KR")}개 영역</strong>
            <small>지수, 금리, 달러, 원자재, 변동성, 신용, 유동성을 분리해서 본다.</small>
            <b>흐름 보기</b>
          </a>
          <a className={topRegimes.length > 0 ? "decision-card is-watch" : "decision-card"} href="#market-regimes">
            <span>체제 신호</span>
            <strong>{topRegimes.length.toLocaleString("ko-KR")}개 주시</strong>
            <small>risk-on/off, 실질금리, 달러 유동성, 에너지 충격 같은 상위 조건이다.</small>
            <b>regime</b>
          </a>
          <Link className="decision-card" href={"/cycle-map" as Route}>
            <span>사이클 연결</span>
            <strong>시장 → 흐름</strong>
            <small>시장 지표 압력이 거시·테마·종목 사이클로 어떻게 내려가는지 이어서 본다.</small>
            <b>흐름 지도</b>
          </Link>
        </div>
      </section>

      <section className="bento-card reveal delay-1" id="market-regimes" aria-label="시장 체제 신호">
        <div className="section-heading stacked-heading">
          <span>먼저 볼 상위 조건</span>
          <h2>현재 켜져 있거나 감시 중인 시장 regime</h2>
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
          <div className="empty-state">활성 또는 감시 중인 시장 regime이 아직 없다. 지표 스냅샷을 먼저 만든다.</div>
        )}
      </section>

      <section className="reveal delay-2" id="market-groups" aria-label="시장 지표 묶음">
        <div style={{ display: "grid", gap: "18px" }}>
          {data.groups.length === 0 ? (
            <article className="empty-state">
              표시할 시장 지표가 없다. cross-asset daily 수집과 regime snapshot을 실행한 뒤 다시 확인한다.
            </article>
          ) : null}
          {data.groups.map((group) => (
            <section className="bento-card" key={group.group_code} aria-label={`${group.group_name} 시장 지표`}>
              <div style={{ display: "flex", justifyContent: "space-between", gap: "18px", alignItems: "flex-end", flexWrap: "wrap", marginBottom: "18px" }}>
                <div>
                  <span className="metric-sub">{group.group_name}</span>
                  <h2 style={{ fontSize: "1.45rem", marginTop: "6px" }}>{group.group_name} 흐름</h2>
                  <p style={{ marginTop: "8px", maxWidth: "760px" }}>{groupSummary(group)}</p>
                </div>
                <span className="relation-pill">
                  최신 {group.fresh_count} · 오래됨 {group.stale_count} · 없음 {group.missing_count}
                </span>
              </div>

              <div className="detail-path-grid" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))" }}>
                {group.indicators.map((indicator) => (
                  <article className={indicatorTone(indicator)} id={`indicator-${indicator.indicator_code}`} key={indicator.indicator_code}>
                    <span>
                      {freshnessLabel(indicator.freshness_status)} · {directionLabel(indicator.shock_direction)}
                    </span>
                    <strong>{indicator.display_name}</strong>
                    <p>{indicator.quality_note_ko || indicator.note_ko}</p>
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px", marginTop: "14px" }}>
                      <small>값 {formatValue(indicator.latest_value)}</small>
                      <small>20일 {formatPercent(indicator.return_20d)}</small>
                      <small>충격 {formatPercent(indicator.shock_magnitude)}</small>
                      <small>신뢰 {formatPercent(indicator.confidence)}</small>
                    </div>
                    <details className="secondary-details" style={{ marginTop: "12px" }}>
                      <summary>원천과 정책</summary>
                      <div className="relationship-list">
                        <div className="relationship-chip">
                          <span>{indicator.preferred_provider}</span>
                          <strong>{indicator.provider_symbol || indicator.indicator_code}</strong>
                          <small>{indicator.source_policy.redistribution_allowed_note}</small>
                        </div>
                        <div className="relationship-chip">
                          <span>{indicator.stale_policy}</span>
                          <strong>{indicator.latest_observation_date || "관측일 없음"}</strong>
                          <small>인과 확정 아님 · 추천 weight 변경 없음</small>
                        </div>
                      </div>
                    </details>
                  </article>
                ))}
              </div>
            </section>
          ))}
        </div>
      </section>

      <section className="bento-card reveal delay-3" id="market-quality" aria-label="시장 지표 품질">
        <div className="section-heading stacked-heading">
          <span>품질 플래그</span>
          <h2>판단 전에 먼저 빼고 봐야 할 것</h2>
          <p>비어 있거나 오래된 지표는 추정값으로 채우지 않는다. 해당 regime 신뢰도를 낮춘다.</p>
        </div>
        {topFlags.length > 0 ? (
          <div className="relationship-list">
            {topFlags.map((flag) => (
              <div className="relationship-chip" key={`${flag.flag_code}-${flag.indicator_code}`}>
                <span>{koCode(flag.severity)} · {freshnessLabel(flag.freshness_status)}</span>
                <strong>{flag.display_name}</strong>
                <small>{flag.message_ko}</small>
              </div>
            ))}
          </div>
        ) : (
          <div className="empty-state">현재 표시할 품질 플래그가 없다.</div>
        )}
      </section>

      <section className="bento-card reveal delay-4" aria-label="뉴스와 시장 지표 연결">
        <div className="section-heading stacked-heading">
          <span>뉴스 연결</span>
          <h2>뉴스와 가격 지표가 같은 시기에 움직였는가</h2>
          <p>아래 연결은 인과 확정이 아니다. 뉴스 해석과 가격 충격이 같은 시간 창에 있었는지 보여주는 근거 후보다.</p>
        </div>
        {data.news_links.length > 0 ? (
          <div className="relationship-list">
            {data.news_links.map((link) => (
              <div className="relationship-chip" key={`${link.document_id}-${link.indicator_code}-${link.link_date}`}>
                <span>{link.indicator_name} · 신뢰 {formatPercent(link.confidence)}</span>
                <strong>{link.title_ko || "제목 미수집"}</strong>
                <small>{link.rationale}</small>
              </div>
            ))}
          </div>
        ) : (
          <div className="empty-state">최근 14일 기준으로 뉴스와 시장 지표 shock 연결이 아직 없다.</div>
        )}
        <div className="btn-row" style={{ marginTop: "18px" }}>
          <Link className="btn btn-primary" href={"/intelligence" as Route}>
            뉴스 AI 보기
          </Link>
          <Link className="btn btn-secondary" href={"/data-health" as Route}>
            수집 상태 보기
          </Link>
        </div>
      </section>
    </div>
  );
}

