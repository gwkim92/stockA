import Link from "next/link";
import type { Route } from "next";

import { getCycleStates } from "@/lib/frontend-api";
import { koCode, koLabel } from "@/lib/korean-labels";

export const dynamic = "force-dynamic";
export const metadata = { title: "사이클" };

function formatConfidence(value: number) {
  return `${Math.round(value * 100)}%`;
}

function formatFeature(value: number | null) {
  if (value === null) {
    return "미측정";
  }
  return `${Math.round(value * 100)}%`;
}

function featureWidth(value: number | null) {
  if (value === null) {
    return "0%";
  }
  return `${Math.min(100, Math.max(0, Math.round(value * 100)))}%`;
}

function themeHref(themeKey: string) {
  return themeKey ? (`/themes/${themeKey}` as Route) : null;
}

function universeLabel(version: string | null | undefined) {
  if (!version || version === "unknown") {
    return "종목군 미확인";
  }
  if (version.startsWith("live-")) {
    return "현재 운영 종목군";
  }
  return `${koCode(version)} 종목군`;
}

export default async function CyclesPage() {
  const response = await getCycleStates();
  const data = response.data;
  const activeCycleCount = data.cycle_states.filter((cycle) => cycle.state !== cycle.previous_state).length;
  const instrumentCount = data.cycle_states.reduce((total, cycle) => total + cycle.instrument_count, 0);
  const averageConfidence =
    data.cycle_states.length > 0
      ? data.cycle_states.reduce((total, cycle) => total + cycle.confidence, 0) / data.cycle_states.length
      : 0;

  return (
    <div className="terminal-page">
      <section className="page-hero reveal" aria-labelledby="cycles-title">
        <div>
          <div className="bento-badge">테마 사이클</div>
          <h1 className="page-title" id="cycles-title">
            사이클은 매수 신호가 아니라 투자 맥락이다.
          </h1>
        </div>
        <p className="page-lede">
          테마 상태는 매수 지시가 아니다. 투자 논리 품질, 커버리지 공백, 증거 검토를 시작할
          운영 맥락으로만 사용한다.
        </p>
        <Link className="btn btn-primary" href={"/cycle-map" as Route}>
          상위 흐름 지도 열기
        </Link>
      </section>

      <section className="status-rail compact-rail reveal delay-1" aria-label="사이클 요약">
        <article className="rail-cell">
          <span>01 전략</span>
          <strong className="rail-word-value">{koCode(data.strategy_name)}</strong>
          <small>{koCode(data.strategy_name)} · {koCode(data.horizon_type)}</small>
        </article>
        <article className="rail-cell">
          <span>02 테마 수</span>
          <strong>{data.cycle_states.length}</strong>
          <small>{universeLabel(data.universe_version)}</small>
        </article>
        <article className="rail-cell">
          <span>03 종목 연결</span>
          <strong>{instrumentCount}</strong>
          <small>테마 종목군 전체</small>
        </article>
        <article className="rail-cell">
          <span>04 평균 신뢰도</span>
          <strong>{formatConfidence(averageConfidence)}</strong>
          <small>{activeCycleCount}개 상태 변화</small>
        </article>
      </section>

      <section className="cycle-index reveal delay-2" aria-label="테마 사이클 목록">
        {data.cycle_states.length === 0 ? (
          <article className="empty-state">
            아직 이 기준일에 저장된 사이클 스냅샷이 없다. 뉴스·상위 흐름은 계속 수집되지만,
            테마 사이클은 일간 신호와 추천 후보가 계산된 뒤 이 화면에 표시된다.
          </article>
        ) : null}
        {data.cycle_states.map((cycle, index) => {
          const href = themeHref(cycle.theme_key);
          return (
            <article className="cycle-row" key={cycle.theme_key}>
              <div className="cycle-number">{String(index + 1).padStart(2, "0")}</div>
              <div className="cycle-main">
                <span>{koCode(cycle.theme_key)}</span>
                <h2>{koLabel(cycle.theme_name)}</h2>
                <p>
                  현재 {koCode(cycle.state)} · 이전 {koCode(cycle.previous_state)} · 신뢰도{" "}
                  {formatConfidence(cycle.confidence)}
                </p>
              </div>
              <div className="cycle-state">
                <strong>{koCode(cycle.state)}</strong>
                <small>{cycle.instrument_count}개 종목</small>
              </div>
              <div className="feature-stack" aria-label={`${cycle.theme_name} 특징`}>
                <div>
                  <span>이벤트</span>
                  <div className="feature-bar">
                    <i style={{ width: featureWidth(cycle.features.event_intensity) }} />
                  </div>
                  <strong>{formatFeature(cycle.features.event_intensity)}</strong>
                </div>
                <div>
                  <span>모멘텀</span>
                  <div className="feature-bar">
                    <i style={{ width: featureWidth(cycle.features.price_momentum) }} />
                  </div>
                  <strong>{formatFeature(cycle.features.price_momentum)}</strong>
                </div>
                <div>
                  <span>품질</span>
                  <div className="feature-bar">
                    <i style={{ width: featureWidth(cycle.features.fundamental_quality) }} />
                  </div>
                  <strong>{formatFeature(cycle.features.fundamental_quality)}</strong>
                </div>
              </div>
              <div className="cycle-actions">
                <small>{cycle.top_symbols.join(" · ")}</small>
                {href ? (
                  <Link className="btn btn-secondary" href={href}>
                    테마 열기
                  </Link>
                ) : (
                  <span className="metric-sub">테마 키 없음</span>
                )}
              </div>
            </article>
          );
        })}
      </section>
    </div>
  );
}
