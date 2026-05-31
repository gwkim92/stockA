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

function cycleChangeLabel(currentState: string, previousState: string) {
  if (currentState === previousState) {
    return "상태 유지";
  }
  return `${koCode(previousState)}에서 ${koCode(currentState)}로 변화`;
}

export default async function CyclesPage() {
  const response = await getCycleStates();
  const data = response.data;
  const activeCycleCount = data.cycle_states.filter((cycle) => cycle.state !== cycle.previous_state).length;
  const instrumentCount = data.cycle_states.reduce((total, cycle) => total + cycle.instrument_count, 0);
  const eventLedThemeCount = data.cycle_states.filter((cycle) => (cycle.features.event_intensity ?? 0) >= 0.65).length;
  const momentumThemeCount = data.cycle_states.filter((cycle) => (cycle.features.price_momentum ?? 0) >= 0.6).length;
  const fundamentalMeasuredCount = data.cycle_states.filter(
    (cycle) => cycle.features.fundamental_quality !== null,
  ).length;
  const missingFeatureCount = data.cycle_states.filter((cycle) =>
    Object.values(cycle.features).some((value) => value === null),
  ).length;
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
            사이클은 매수 신호가 아니라 투자 논리 점검 지도다.
          </h1>
        </div>
        <p className="page-lede">
          테마 상태만 보고 매수·매도를 결정하지 않는다. 뉴스 흐름, 가격 흐름, 기업 품질을 나눠 보고
          기존 추천·보유 투자 논리와 충돌하는지 확인하는 출발점으로 사용한다.
        </p>
        <Link className="btn btn-primary" href={"/cycle-map" as Route}>
          상위 흐름 지도 열기
        </Link>
      </section>

      <section className="cycle-command-panel reveal delay-1" aria-labelledby="cycle-command-title">
        <div className="cycle-command-lead">
          <span>사이클 판정판</span>
          <h2 id="cycle-command-title">상태, 근거, 추천 영향을 분리해서 본다.</h2>
          <p>
            이 화면은 테마별 사이클 상태표다. 어떤 테마가 변했는지 먼저 보고, 왜 변했는지는
            상위 흐름 지도와 테마 상세에서 뉴스·AI 근거·연결 종목을 이어서 확인한다.
          </p>
        </div>
        <div className="cycle-command-grid">
          <a className="cycle-command-card ready" href="#cycle-states">
            <span>01</span>
            <small>상태표</small>
            <strong>{data.cycle_states.length}개 테마</strong>
            <em>{universeLabel(data.universe_version)}</em>
            <p>테마별 상태를 한 번에 본다. 이 표는 매수·매도 결론이 아니라 투자 논리 점검 출발점이다.</p>
            <b>상태표 보기</b>
          </a>
          <a className={activeCycleCount > 0 ? "cycle-command-card watch" : "cycle-command-card ready"} href="#cycle-states">
            <span>02</span>
            <small>변화</small>
            <strong>{activeCycleCount}개 상태 변화</strong>
            <em>현재 상태와 이전 상태 비교</em>
            <p>
              상태가 바뀐 테마는 추천·보유 투자 논리와 충돌하는지 먼저 본다. 변화가 없어도 신뢰도와 근거
              축은 별도로 확인한다.
            </p>
            <b>변화 항목 보기</b>
          </a>
          <a className={missingFeatureCount > 0 ? "cycle-command-card watch" : "cycle-command-card ready"} href="#cycle-states">
            <span>03</span>
            <small>판단 근거</small>
            <strong>뉴스 {eventLedThemeCount} · 가격 {momentumThemeCount}</strong>
            <em>재무 품질 {fundamentalMeasuredCount}/{data.cycle_states.length}</em>
            <p>
              막대는 뉴스 흐름, 가격 흐름, 기업 품질을 분리해 보여준다. 특정 축이 비어 있으면 결론보다
              데이터 보강이 먼저다.
            </p>
            <b>판단 근거 확인</b>
          </a>
          <Link className="cycle-command-card" href={"/cycle-map" as Route}>
            <span>04</span>
            <small>원인 경로</small>
            <strong>상위 흐름 지도</strong>
            <em>거시 → 도메인 → 테마 → 종목</em>
            <p>
              사이클 상태의 배경은 지도에서 본다. 뉴스가 어떤 상위 흐름을 거쳐 테마와 종목으로 이어졌는지
              확인하는 화면이다.
            </p>
            <b>흐름 지도 열기</b>
          </Link>
        </div>
      </section>

      <section className="status-rail compact-rail reveal delay-1" aria-label="사이클 요약">
        <article className="rail-cell">
          <span>전략</span>
          <strong className="rail-word-value">{koCode(data.strategy_name)}</strong>
          <small>{koCode(data.strategy_name)} · {koCode(data.horizon_type)}</small>
        </article>
        <article className="rail-cell">
          <span>테마 수</span>
          <strong>{data.cycle_states.length}</strong>
          <small>{universeLabel(data.universe_version)}</small>
        </article>
        <article className="rail-cell">
          <span>연결 종목</span>
          <strong>{instrumentCount}</strong>
          <small>테마 종목군 전체</small>
        </article>
        <article className="rail-cell">
          <span>평균 신뢰도</span>
          <strong>{formatConfidence(averageConfidence)}</strong>
          <small>{activeCycleCount}개 상태 변화</small>
        </article>
      </section>

      <section className="cycle-index reveal delay-2" id="cycle-states" aria-label="테마 사이클 목록">
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
                  {cycleChangeLabel(cycle.state, cycle.previous_state)} · 신뢰도{" "}
                  {formatConfidence(cycle.confidence)}
                </p>
              </div>
              <div className="cycle-state">
                <strong>{koCode(cycle.state)}</strong>
                <small>{cycle.instrument_count}개 종목</small>
              </div>
              <div className="feature-stack" aria-label={`${cycle.theme_name} 특징`}>
                <div>
                  <span>뉴스 흐름</span>
                  <div className="feature-bar">
                    <i style={{ width: featureWidth(cycle.features.event_intensity) }} />
                  </div>
                  <strong>{formatFeature(cycle.features.event_intensity)}</strong>
                </div>
                <div>
                  <span>가격 흐름</span>
                  <div className="feature-bar">
                    <i style={{ width: featureWidth(cycle.features.price_momentum) }} />
                  </div>
                  <strong>{formatFeature(cycle.features.price_momentum)}</strong>
                </div>
                <div>
                  <span>기업 품질</span>
                  <div className="feature-bar">
                    <i style={{ width: featureWidth(cycle.features.fundamental_quality) }} />
                  </div>
                  <strong>{formatFeature(cycle.features.fundamental_quality)}</strong>
                </div>
              </div>
              <div className="cycle-actions">
                <small>{cycle.top_symbols.length > 0 ? cycle.top_symbols.join(" · ") : "연결 종목 없음"}</small>
                {href ? (
                  <Link className="btn btn-secondary" href={href}>
                    테마 상세 보기
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
