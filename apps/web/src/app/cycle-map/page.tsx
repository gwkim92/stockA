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
    <div className="terminal-page">
      <section className="page-hero reveal" aria-labelledby="cycle-map-title">
        <div>
          <div className="bento-badge">흐름 지도</div>
          <h1 className="page-title" id="cycle-map-title">
            시장 흐름이 어떤 종목까지 내려가는지 한 장으로 본다.
          </h1>
        </div>
        <p className="page-lede">
          뉴스는 개별 종목 뉴스와 상위 흐름 뉴스로 나뉜다. 이 화면은 거시, 도메인, 테마, 종목 신호가
          어떤 계층으로 연결되고 추천 근거에 들어가는지 보여주는 지도다.
        </p>
      </section>

      <section className="cycle-map-path-panel reveal delay-1" aria-labelledby="cycle-map-path-title">
        <div className="cycle-map-path-lead">
          <span>흐름 경로 현황판</span>
          <h2 id="cycle-map-path-title">뉴스가 어느 흐름을 거쳐 종목에 닿았는지 본다.</h2>
          <p>
            사이클 상태표가 테마별 현재 상태를 보여준다면, 이 화면은 원인 경로 지도다. 원천 뉴스와
            AI 구조화가 어떤 상위 흐름으로 묶였고, 그 흐름이 어느 종목·추천 근거로 내려갔는지 추적한다.
          </p>
        </div>
        <div className="cycle-map-path-grid">
          <Link className="cycle-map-path-card ready" href={"/intelligence" as Route}>
            <span>01</span>
            <small>원천 뉴스</small>
            <strong>{data.summary.direct_event_count}개 뉴스 영향</strong>
            <em>AI 근거 흐름 {aiBackedNodeCount}개</em>
            <p>
              먼저 어떤 뉴스와 AI 구조화 결과가 흐름을 만들었는지 본다. 번역·검증 결과는 뉴스·AI 근거
              화면에서 이어서 확인한다.
            </p>
            <b>뉴스 AI 보기</b>
          </Link>
          <a className="cycle-map-path-card ready" href="#cycle-map-layers">
            <span>02</span>
            <small>흐름 항목</small>
            <strong>{data.summary.node_count}개 흐름 항목</strong>
            <em>거시 {data.summary.macro_count} · 테마 {data.summary.theme_count}</em>
            <p>
              거시, 도메인, 섹터, 테마, 종목 흐름을 계층으로 본다. 항목이 많아도 핵심은 위에서 아래로
              내려가는 경로다.
            </p>
            <b>흐름 경로 보기</b>
          </a>
          <a className={conflictNodeCount > 0 ? "cycle-map-path-card watch" : "cycle-map-path-card ready"} href="#cycle-map-layers">
            <span>03</span>
            <small>종목 노출</small>
            <strong>{exposedNodeCount}개 흐름 연결</strong>
            <em>충돌 표시 {conflictNodeCount}개</em>
            <p>
              상위 흐름이 바로 매수 신호가 되지는 않는다. 어떤 종목이 노출됐고, 충돌이나 불확실성이
              있는지 같이 본다.
            </p>
            <b>노출 종목 확인</b>
          </a>
          <Link
            className={data.summary.recommendation_count > 0 ? "cycle-map-path-card ready" : "cycle-map-path-card watch"}
            href={"/recommendations" as Route}
          >
            <span>04</span>
            <small>추천 연결</small>
            <strong>{data.summary.recommendation_count}개 추천</strong>
            <em>투자 논리 {data.summary.thesis_count}개</em>
            <p>
              추천은 이 지도만으로 결정하지 않는다. 추천 상세에서 직접 뉴스, 상위 흐름 연결, 재무·밸류에이션,
              가상 매매 검증을 분리해 본다.
            </p>
            <b>추천 근거 보기</b>
          </Link>
        </div>
      </section>

      <section className="status-rail compact-rail reveal delay-1" aria-label="흐름 지도 요약">
        <article className="rail-cell">
          <span>상위 흐름</span>
          <strong>{data.summary.node_count}</strong>
          <small>거시 {data.summary.macro_count} · 도메인 {data.summary.domain_count} · 테마 {data.summary.theme_count}</small>
        </article>
        <article className="rail-cell">
          <span>뉴스 영향</span>
          <strong>{data.summary.direct_event_count}</strong>
          <small>연결 영향 {data.summary.propagated_impact_count}개</small>
        </article>
        <article className="rail-cell">
          <span>추천 연결</span>
          <strong>{data.summary.recommendation_count}</strong>
          <small>투자 논리 {data.summary.thesis_count}개</small>
        </article>
        <article className="rail-cell">
          <span>가장 뜨거운 흐름</span>
          <strong className="rail-word-value">{hotNode ? koCode(hotNode.node_code) : "대기"}</strong>
          <small>{hotNode ? `${koCode(hotNode.cycle_state)} · 열기 ${formatPercent(nodeHeat(hotNode))}` : data.as_of_date}</small>
        </article>
      </section>

      <section className="bento-card reveal delay-1" aria-label="흐름 지도 읽는 법">
        <div className="section-heading stacked-heading">
          <span>읽는 순서</span>
          <h2>뉴스에서 추천까지 내려가는 경로</h2>
          <p>이 지도는 매수 신호가 아니다. 상위 흐름이 어떤 흐름 단계를 거쳐 어느 종목군과 추천 상세 근거에 닿는지 확인하는 화면이다.</p>
        </div>
        <div className="flow-steps">
          <article className="flow-step">
            <span>01</span>
            <strong>거시</strong>
            <p>금리, 물가, 유동성, 성장 같은 최상위 환경을 먼저 본다.</p>
          </article>
          <article className="flow-step">
            <span>02</span>
            <strong>도메인</strong>
            <p>기술, 에너지처럼 큰 사업 영역이 거시 흐름을 어떻게 받는지 본다.</p>
          </article>
          <article className="flow-step">
            <span>03</span>
            <strong>테마</strong>
            <p>AI 반도체, 양자컴퓨팅, 에너지 지정학 같은 실제 투자 테마로 좁힌다.</p>
          </article>
          <article className="flow-step">
            <span>04</span>
            <strong>종목</strong>
            <p>노출도와 직접 뉴스가 있는 종목 신호로 연결한다.</p>
          </article>
          <article className="flow-step">
            <span>05</span>
            <strong>검증</strong>
            <p>추천 상세와 보유 상태에서 점수, 투자 논리, 거래 안전을 따로 확인한다.</p>
          </article>
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
