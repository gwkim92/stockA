import Link from "next/link";
import type { Route } from "next";

import { getCycleMap } from "@/lib/frontend-api";
import { koCode, koLabel } from "@/lib/korean-labels";
import type { CycleMapData } from "@/lib/types";

export const dynamic = "force-dynamic";
export const metadata = { title: "흐름 지도" };

type CycleNode = CycleMapData["nodes"][number];

const LEVEL_ORDER = ["macro", "domain", "sector", "theme", "instrument", "unknown"] as const;

function formatPercent(value: number | null | undefined) {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return "미측정";
  }
  return `${Math.round(value * 1000) / 10}%`;
}

function levelTitle(level: string) {
  if (level === "macro") {
    return "거시";
  }
  if (level === "domain") {
    return "도메인";
  }
  if (level === "sector") {
    return "섹터";
  }
  if (level === "theme") {
    return "테마";
  }
  if (level === "instrument") {
    return "종목";
  }
  return "기타";
}

function nodeHref(nodeCode: string) {
  return `/themes/${encodeURIComponent(nodeCode)}` as Route;
}

function stockHref(symbol: string) {
  return `/stocks/${encodeURIComponent(symbol)}` as Route;
}

function nodeHeat(node: CycleNode) {
  return node.event_heat_score ?? node.cycle_score ?? 0;
}

function relationCount(data: CycleMapData, nodeCode: string) {
  return data.edges.filter((edge) => edge.parent_code === nodeCode || edge.child_code === nodeCode).length;
}

function nodeSummary(node: CycleNode) {
  const name = koCode(node.node_code);
  const state = koCode(node.cycle_state);
  const directEvents = node.counts.direct_event_count;
  const propagatedImpacts = node.counts.propagated_impact_count;
  const symbolCount = node.top_symbols.length;
  const recommendationCount = node.counts.recommendation_count;

  return `${name}. 현재 상태는 ${state}. 최근 뉴스 ${directEvents}건, 상위 흐름 연결 영향 ${propagatedImpacts}건, 연결 종목 ${symbolCount}개, 추천 연결 ${recommendationCount}건을 함께 확인한다.`;
}

function groupedNodes(nodes: CycleNode[]) {
  return LEVEL_ORDER.map((level) => ({
    level,
    title: levelTitle(level),
    nodes: nodes.filter((node) => node.cycle_level === level),
  })).filter((group) => group.nodes.length > 0);
}

export default async function CycleMapPage() {
  const response = await getCycleMap();
  const data = response.data;
  const groups = groupedNodes(data.nodes);
  const hotNode = data.nodes.find((node) => node.node_code === data.summary.hot_node_code) ?? data.nodes[0] ?? null;
  const exposedNodeCount = data.nodes.filter((node) => node.counts.exposed_instrument_count > 0).length;
  const aiBackedNodeCount = data.nodes.filter((node) => node.counts.ai_artifact_count > 0).length;
  const conflictNodeCount = data.nodes.filter((node) => node.conflict_flags.length > 0).length;

  return (
    <div className="terminal-page decision-page">
      <section className="decision-brief reveal" aria-labelledby="cycle-map-title">
        <div className="decision-brief-main">
          <span className="decision-brief-kicker">흐름 지도 · {data.as_of_date}</span>
          <h1 className="decision-brief-title" id="cycle-map-title">
            현재 가장 뜨거운 흐름: {hotNode ? koCode(hotNode.node_code) : "아직 대기"}
          </h1>
          <p className="decision-brief-copy">
            이 지도는 매수 신호가 아니다. 뉴스가 거시·도메인·테마를 거쳐 어떤 종목과 추천 근거로 내려가는지
            확인하는 경로 화면이다.
          </p>
          <div className="decision-brief-meta" aria-label="흐름 지도 핵심 상태">
            <span>흐름 {data.summary.node_count.toLocaleString("ko-KR")}개</span>
            <span>뉴스 영향 {data.summary.direct_event_count.toLocaleString("ko-KR")}개</span>
            <span>추천 연결 {data.summary.recommendation_count.toLocaleString("ko-KR")}개</span>
            <span>충돌 {conflictNodeCount.toLocaleString("ko-KR")}개</span>
          </div>
        </div>
        <div className="decision-brief-grid">
          <Link className="decision-card is-good" href={"/intelligence" as Route}>
            <span>원천 뉴스</span>
            <strong>{data.summary.direct_event_count.toLocaleString("ko-KR")}개 영향</strong>
            <small>AI 근거가 붙은 흐름 {aiBackedNodeCount.toLocaleString("ko-KR")}개. 번역과 검증은 뉴스·AI에서 본다.</small>
            <b>뉴스 AI</b>
          </Link>
          <a className="decision-card is-good" href="#cycle-map-layers">
            <span>흐름 항목</span>
            <strong>{data.summary.node_count.toLocaleString("ko-KR")}개</strong>
            <small>거시 {data.summary.macro_count.toLocaleString("ko-KR")}개 · 테마 {data.summary.theme_count.toLocaleString("ko-KR")}개</small>
            <b>경로 보기</b>
          </a>
          <a className={conflictNodeCount > 0 ? "decision-card is-watch" : "decision-card is-good"} href="#cycle-map-layers">
            <span>종목 노출</span>
            <strong>{exposedNodeCount.toLocaleString("ko-KR")}개 연결</strong>
            <small>상위 흐름은 바로 매수 신호가 아니다. 노출 종목과 충돌 표시를 같이 본다.</small>
            <b>종목 확인</b>
          </a>
          <Link className={data.summary.recommendation_count > 0 ? "decision-card is-good" : "decision-card is-watch"} href={"/recommendations" as Route}>
            <span>추천 연결</span>
            <strong>{data.summary.recommendation_count.toLocaleString("ko-KR")}개</strong>
            <small>추천 상세에서 뉴스, 흐름, 재무, 가상 매매 검증을 다시 분리한다.</small>
            <b>추천 근거</b>
          </Link>
        </div>
      </section>

      <section className="reveal delay-2" id="cycle-map-layers" aria-label="계층형 사이클 지도">
        {groups.length === 0 ? (
          <article className="empty-state">
            아직 표시할 계층형 사이클 스냅샷이 없다. 뉴스 수집, AI 구조화, 상위 흐름 연결, 사이클 스냅샷 실행 후 이 화면이 채워진다.
          </article>
        ) : null}

        <div style={{ display: "grid", gap: "18px" }}>
          {groups.map((group) => (
            <section className="bento-card" key={group.level} aria-label={`${group.title} 흐름`}>
              <div style={{ display: "flex", justifyContent: "space-between", gap: "18px", alignItems: "flex-end", flexWrap: "wrap", marginBottom: "18px" }}>
                <div>
                  <span className="metric-sub">{group.title} 단계</span>
                  <h2 style={{ fontSize: "1.45rem", marginTop: "6px" }}>{group.title}에서 현재 움직이는 흐름</h2>
                </div>
                <span className="relation-pill">{group.nodes.length}개 흐름 항목</span>
              </div>

              <div className="detail-path-grid" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))" }}>
                {group.nodes.map((node) => (
                  <article className="detail-path-card" key={node.node_code}>
                    <span>{koCode(node.cycle_state)} · {formatPercent(node.cycle_score)}</span>
                    <strong>{koCode(node.node_code)}</strong>
                    <p>{nodeSummary(node)}</p>

                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px", marginTop: "14px" }}>
                      <small>뉴스 {node.counts.direct_event_count}</small>
                      <small>연결 영향 {node.counts.propagated_impact_count}</small>
                      <small>추천 {node.counts.recommendation_count}</small>
                      <small>관계 {relationCount(data, node.node_code)}</small>
                    </div>

                    {node.top_symbols.length > 0 ? (
                      <div className="relationship-list" aria-label={`${node.node_code} 연결 종목`}>
                        {node.top_symbols.slice(0, 5).map((symbol) => (
                          <Link className="relationship-chip" href={stockHref(symbol)} key={`${node.node_code}-${symbol}`}>
                            <span>종목</span>
                            <strong>{koCode(symbol)}</strong>
                          </Link>
                        ))}
                      </div>
                    ) : null}

                    {node.recent_event_titles.length > 0 ? (
                      <details className="secondary-details" style={{ marginTop: "12px" }}>
                        <summary>최근 근거 뉴스</summary>
                        <div className="relationship-list">
                          {node.recent_event_titles.slice(0, 3).map((title) => (
                            <div className="relationship-chip" key={`${node.node_code}-${title}`}>
                              <span>뉴스</span>
                              <strong>{koLabel(title)}</strong>
                            </div>
                          ))}
                        </div>
                      </details>
                    ) : null}

                    <div className="btn-row" style={{ marginTop: "14px" }}>
                      <Link className="btn btn-primary" href={nodeHref(node.node_code)}>
                        흐름 상세
                      </Link>
                      {node.top_symbols[0] ? (
                        <Link className="btn btn-secondary" href={stockHref(node.top_symbols[0])}>
                          대표 종목
                        </Link>
                      ) : null}
                    </div>
                  </article>
                ))}
              </div>
            </section>
          ))}
        </div>
      </section>

      <section className="bento-card reveal delay-3" aria-label="흐름 관계">
        <div className="section-heading stacked-heading">
          <span>관계선</span>
          <h2>상위 흐름이 아래 흐름으로 이어지는 규칙</h2>
          <p>관계선은 AI가 즉석에서 만든 말이 아니라 사전에 정한 시장 분류 지도를 읽어 보여준다.</p>
        </div>
        {data.edges.length > 0 ? (
          <div className="relationship-list">
            {data.edges.slice(0, 24).map((edge) => (
              <div className="relationship-chip" key={`${edge.parent_code}-${edge.child_code}-${edge.relation_type}`}>
                <span>{koCode(edge.relation_type)} · {formatPercent(edge.weight)}</span>
                <strong>{koCode(edge.parent_code)} → {koCode(edge.child_code)}</strong>
                <small>{koCode(edge.parent_code)}에서 {koCode(edge.child_code)} 방향으로 이어지는 흐름이다.</small>
              </div>
            ))}
          </div>
        ) : (
          <div className="empty-state">현재 기준일에 표시할 흐름 관계가 없다.</div>
        )}
      </section>
    </div>
  );
}
