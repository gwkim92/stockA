import Link from "next/link";
import type { Route } from "next";

import { getCycleMap, getCycleStates } from "@/lib/frontend-api";
import { koCode, koLabel } from "@/lib/korean-labels";
import type { CycleMapData, CycleStateListData } from "@/lib/types";

export const dynamic = "force-dynamic";
export const metadata = { title: "흐름 지도" };

type CycleNode = CycleMapData["nodes"][number];
type CycleState = CycleStateListData["cycle_states"][number];

const LEVEL_ORDER = ["macro", "domain", "sector", "theme", "instrument", "unknown"] as const;
const HIGH_EVENT_THRESHOLD = 0.55;
const HIGH_SCORE_THRESHOLD = 0.6;

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

function formatCount(value: number) {
  return value.toLocaleString("ko-KR");
}

function shortText(value: string | null | undefined, fallback: string) {
  const text = koLabel(value || fallback).trim();
  return text.length > 140 ? `${text.slice(0, 140)}...` : text;
}

function cycleAttentionScore(node: CycleNode) {
  const heat = node.event_heat_score ?? 0;
  const cycleScore = node.cycle_score ?? 0;
  const propagation = Math.min(1, node.counts.propagated_impact_count / 80);
  const recommendations = Math.min(1, node.counts.recommendation_count / 20);
  const conflicts = node.conflict_flags.length > 0 ? 0.22 : 0;
  return heat * 0.34 + cycleScore * 0.22 + propagation * 0.2 + recommendations * 0.14 + conflicts;
}

function nodeTone(node: CycleNode) {
  if (node.conflict_flags.length > 0) {
    return "tone-watch";
  }
  if ((node.cycle_score ?? 0) >= HIGH_SCORE_THRESHOLD || nodeHeat(node) >= HIGH_EVENT_THRESHOLD) {
    return "tone-ready";
  }
  return "tone-neutral";
}

function nodeDecisionLabel(node: CycleNode) {
  if (node.conflict_flags.length > 0) {
    return "충돌 먼저 확인";
  }
  if (node.counts.direct_event_count >= 20) {
    return "뉴스 원천 확인";
  }
  if (node.counts.propagated_impact_count > 0) {
    return "전파 종목 확인";
  }
  if (node.counts.recommendation_count > 0) {
    return "추천 영향 확인";
  }
  return "관찰 유지";
}

function topNodeLabel(node: CycleNode | null) {
  if (!node) {
    return "사이클 데이터 대기";
  }
  return koCode(node.node_code);
}

function nodeQuestion(node: CycleNode) {
  if (node.cycle_level === "macro") {
    return "이 거시 흐름이 성장주, 채권, 원자재, 현금성 자산 중 어디에 압력을 주는가?";
  }
  if (node.cycle_level === "domain") {
    return "상위 거시 흐름이 이 산업 도메인의 수요·마진·밸류에이션을 밀어주는가?";
  }
  if (node.cycle_level === "sector") {
    return "섹터 ETF와 주요 구성 종목이 같은 방향으로 움직이는가?";
  }
  if (node.cycle_level === "theme") {
    return "테마 뉴스가 실제 종목 실적과 가격 흐름으로 내려오고 있는가?";
  }
  return "종목 자체 흐름이 상위 사이클과 같은 방향인가?";
}

function nodeDriverText(node: CycleNode) {
  if (node.parent_codes.length > 0) {
    return node.parent_codes.slice(0, 2).map(koCode).join(" · ");
  }
  if (node.cycle_level === "macro") {
    return "거시 뉴스와 시장 지표";
  }
  return `${levelTitle(node.cycle_level)} 자체 흐름`;
}

function nodeDownstreamText(node: CycleNode) {
  if (node.child_codes.length > 0) {
    return node.child_codes.slice(0, 2).map(koCode).join(" · ");
  }
  if (node.top_symbols.length > 0) {
    return node.top_symbols.slice(0, 3).map(koCode).join(" · ");
  }
  return "아직 하위 노출 대기";
}

function nodeEvidenceLine(node: CycleNode) {
  return `뉴스 ${formatCount(node.counts.direct_event_count)} · 전파 ${formatCount(node.counts.propagated_impact_count)} · 추천 ${formatCount(node.counts.recommendation_count)}`;
}

function nodeNextAction(node: CycleNode) {
  if (node.counts.recommendation_count > 0) {
    return "추천 상세에서 근거가 실제 점수와 어떻게 분리됐는지 확인한다.";
  }
  if (node.top_symbols.length > 0) {
    return "대표 종목 상세에서 직접 뉴스, 상위 흐름, 시장 동조성을 확인한다.";
  }
  if (node.counts.direct_event_count > 0) {
    return "뉴스 근거 화면에서 원천 뉴스와 종목·테마 영향을 먼저 확인한다.";
  }
  return "다음 뉴스/가격 수집 후 상태 변화를 기다린다.";
}

function flowPathText(data: CycleMapData, node: CycleNode) {
  const parent = data.edges.find((edge) => edge.child_code === node.node_code)?.parent_code;
  const child = data.edges.find((edge) => edge.parent_code === node.node_code)?.child_code;
  return [parent, node.node_code, child].filter(Boolean).map(koCode).join(" → ");
}

function cycleStateForNode(states: Map<string, CycleState>, node: CycleNode) {
  return states.get(node.node_code) ?? null;
}

function nodeSummary(node: CycleNode) {
  const name = koCode(node.node_code);
  const state = koCode(node.cycle_state);
  const directEvents = node.counts.direct_event_count;
  const propagatedImpacts = node.counts.propagated_impact_count;
  const symbolCount = node.top_symbols.length;
  const recommendationCount = node.counts.recommendation_count;

  return `${name}. 현재 상태는 ${state}. 최근 뉴스 ${directEvents}건, 상위 흐름 영향 ${propagatedImpacts}건, 연결 종목 ${symbolCount}개, 추천 영향 ${recommendationCount}건을 함께 확인한다.`;
}

function groupedNodes(nodes: CycleNode[]) {
  return LEVEL_ORDER.map((level) => ({
    level,
    title: levelTitle(level),
    nodes: nodes.filter((node) => node.cycle_level === level),
  })).filter((group) => group.nodes.length > 0);
}

export default async function CycleMapPage() {
  const [response, cycleStateResponse] = await Promise.all([getCycleMap(), getCycleStates()]);
  const data = response.data;
  const cycleStates = cycleStateResponse.data.cycle_states;
  const cycleStatesByKey = new Map(cycleStates.map((cycle) => [cycle.theme_key, cycle]));
  const groups = groupedNodes(data.nodes);
  const exposedNodeCount = data.nodes.filter((node) => node.counts.exposed_instrument_count > 0).length;
  const aiBackedNodeCount = data.nodes.filter((node) => node.counts.ai_artifact_count > 0).length;
  const conflictNodeCount = data.nodes.filter((node) => node.conflict_flags.length > 0).length;
  const attentionNodes = [...data.nodes].sort((left, right) => cycleAttentionScore(right) - cycleAttentionScore(left)).slice(0, 6);
  const pathNodes = [...data.nodes].sort((left, right) => cycleAttentionScore(right) - cycleAttentionScore(left)).slice(0, 10);
  const hotNode = attentionNodes[0] ?? data.nodes.find((node) => node.node_code === data.summary.hot_node_code) ?? null;
  const turningCycles = cycleStates.filter((cycle) => cycle.state !== cycle.previous_state).slice(0, 5);
  const eventLedCycles = [...cycleStates]
    .sort((left, right) => (right.features.event_intensity ?? 0) - (left.features.event_intensity ?? 0))
    .slice(0, 4);
  const evidenceGapCount = cycleStates.filter((cycle) =>
    Object.values(cycle.features).some((value) => value === null),
  ).length;
  const symbolGapCount = data.nodes.filter((node) => node.counts.exposed_instrument_count === 0).length;

  return (
    <div className="terminal-page decision-page cycle-map-page research-command-page">
      <section className="decision-brief reveal research-command-deck cycle-command-deck" aria-labelledby="cycle-map-title">
        <div className="decision-brief-main">
          <span className="decision-brief-kicker">흐름 지도 · {data.as_of_date}</span>
          <h1 className="decision-brief-title" id="cycle-map-title">
            오늘은 {topNodeLabel(hotNode)}부터 본다.
          </h1>
          <p className="decision-brief-copy">
            먼저 상위 흐름의 열기와 충돌을 보고, 그 흐름이 어떤 종목과 추천 근거로 내려가는지 확인한다.
          </p>
          <div className="decision-brief-meta" aria-label="흐름 지도 핵심 상태">
            <span>흐름 {data.summary.node_count.toLocaleString("ko-KR")}개</span>
            <span>뉴스 영향 {data.summary.direct_event_count.toLocaleString("ko-KR")}개</span>
            <span>추천 영향 {data.summary.recommendation_count.toLocaleString("ko-KR")}개</span>
            <span>충돌 {conflictNodeCount.toLocaleString("ko-KR")}개</span>
            <span>노출 대기 {symbolGapCount.toLocaleString("ko-KR")}개</span>
          </div>
        </div>
        <div className="decision-brief-grid">
          <Link className="decision-card is-good" href={"/intelligence" as Route}>
            <span>원천 뉴스</span>
            <strong>{data.summary.direct_event_count.toLocaleString("ko-KR")}개 영향</strong>
            <small>근거가 붙은 흐름 {aiBackedNodeCount.toLocaleString("ko-KR")}개. 원문·한국어 요약·품질 결과는 뉴스 근거에서 본다.</small>
            <b>뉴스 근거</b>
          </Link>
          <a className="decision-card is-good" href="#cycle-map-layers">
            <span>사이클 경로</span>
            <strong>{data.summary.node_count.toLocaleString("ko-KR")}개</strong>
            <small>거시 {data.summary.macro_count.toLocaleString("ko-KR")}개 · 테마 {data.summary.theme_count.toLocaleString("ko-KR")}개</small>
            <b>경로 보기</b>
          </a>
          <Link className="decision-card is-good" href={"/cycles" as Route}>
            <span>상태표</span>
            <strong>테마별 사이클</strong>
            <small>뉴스 흐름, 가격 흐름, 기업 품질을 나눠 테마 상태 변화를 확인한다.</small>
            <b>상태표 열기</b>
          </Link>
          <a className={conflictNodeCount > 0 ? "decision-card is-watch" : "decision-card is-good"} href="#cycle-map-layers">
            <span>종목 노출</span>
            <strong>{exposedNodeCount.toLocaleString("ko-KR")}개 연결</strong>
            <small>상위 흐름이 어떤 종목으로 내려가는지 보고, 종목 상세에서 직접 근거를 확인한다.</small>
            <b>종목 확인</b>
          </a>
          <Link className={data.summary.recommendation_count > 0 ? "decision-card is-good" : "decision-card is-watch"} href={"/recommendations" as Route}>
            <span>추천 영향</span>
            <strong>{data.summary.recommendation_count.toLocaleString("ko-KR")}개</strong>
            <small>추천 상세에서 뉴스, 흐름, 재무, 가상 매매 검증을 다시 분리한다.</small>
            <b>추천 근거</b>
          </Link>
        </div>
      </section>

      <section className="cycle-operating-board reveal delay-1" aria-labelledby="cycle-operating-title">
        <div className="cycle-attention-panel">
          <div className="section-heading stacked-heading">
            <span>우선순위</span>
            <h2 id="cycle-operating-title">오늘 가장 먼저 읽을 사이클</h2>
            <p>
              뉴스 열기, 전파 영향, 추천 영향, 충돌 표시를 합쳐 먼저 볼 흐름을 정렬했다.
              왼쪽부터 무엇이 움직였는지, 어디로 내려가는지, 무엇을 확인할지 순서로 읽는다.
            </p>
          </div>
          <div className="cycle-attention-list">
            {attentionNodes.map((node, index) => {
              const linkedState = cycleStateForNode(cycleStatesByKey, node);
              return (
                <article className={`cycle-attention-card ${nodeTone(node)}`} key={node.node_code}>
                  <div className="cycle-attention-rank">{String(index + 1).padStart(2, "0")}</div>
                  <div className="cycle-attention-main">
                    <span>{levelTitle(node.cycle_level)} · {nodeDecisionLabel(node)}</span>
                    <strong>{koCode(node.node_code)}</strong>
                    <p>{shortText(node.summary_text_ko, nodeSummary(node))}</p>
                    <div className="cycle-path-tape">{flowPathText(data, node) || koCode(node.node_code)}</div>
                  </div>
                  <div className="cycle-attention-metrics">
                    <div>
                      <span>상태</span>
                      <strong>{koCode(linkedState?.state ?? node.cycle_state)}</strong>
                    </div>
                    <div>
                      <span>뉴스</span>
                      <strong>{formatCount(node.counts.direct_event_count)}</strong>
                    </div>
                    <div>
                      <span>전파</span>
                      <strong>{formatCount(node.counts.propagated_impact_count)}</strong>
                    </div>
                    <div>
                      <span>추천</span>
                      <strong>{formatCount(node.counts.recommendation_count)}</strong>
                    </div>
                  </div>
                  <div className="cycle-attention-actions">
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
              );
            })}
          </div>
        </div>

        <aside className="cycle-command-aside" aria-label="사이클 읽는 방법">
          <article className="cycle-playbook">
            <span>읽는 순서</span>
            <strong>상위 흐름 → 전파 → 종목 → 추천</strong>
            <p>거시 뉴스는 종목을 억지로 붙이지 않는다. 먼저 상위 사이클로 저장하고 노출도 규칙으로 종목 영향 후보를 만든다.</p>
          </article>
          <article className="cycle-playbook">
            <span>전환 감시</span>
            <strong>{turningCycles.length.toLocaleString("ko-KR")}개 변화</strong>
            <p>{turningCycles.length > 0 ? turningCycles.map((cycle) => koCode(cycle.theme_key)).join(" · ") : "오늘 상태가 바뀐 테마는 없다."}</p>
          </article>
          <article className="cycle-playbook">
            <span>뉴스 주도</span>
            <strong>{eventLedCycles.length.toLocaleString("ko-KR")}개 상위</strong>
            <p>{eventLedCycles.map((cycle) => koCode(cycle.theme_key)).join(" · ")}</p>
          </article>
          <article className="cycle-playbook warning">
            <span>데이터 공백</span>
            <strong>{evidenceGapCount.toLocaleString("ko-KR")}개 · 노출 대기 {symbolGapCount.toLocaleString("ko-KR")}개</strong>
            <p>뉴스, 가격, 기업 품질, 종목 노출 중 빈 축이 있으면 결론보다 수집·전파 보강이 먼저다.</p>
          </article>
        </aside>
      </section>

      <section className="cycle-lane-board reveal delay-2" aria-labelledby="cycle-lane-title">
        <div className="section-heading stacked-heading">
          <span>계층 지도</span>
          <h2 id="cycle-lane-title">사이클은 위에서 아래로 내려오며 종목 근거가 된다</h2>
          <p>각 레인은 거시, 도메인, 섹터, 테마를 분리한다. 같은 줄에 있어도 의미가 다르므로 바로 종목 추천으로 해석하지 않는다.</p>
        </div>
        <div className="cycle-lanes">
          {groups.map((group) => (
            <section className="cycle-lane" key={group.level} aria-label={`${group.title} 사이클 레인`}>
              <div className="cycle-lane-head">
                <span>{group.title}</span>
                <strong>{group.nodes.length}개</strong>
              </div>
              <div className="cycle-node-stack">
                {group.nodes
                  .sort((left, right) => cycleAttentionScore(right) - cycleAttentionScore(left))
                  .slice(0, 6)
                  .map((node) => (
                    <Link className={`cycle-node-card ${nodeTone(node)}`} href={nodeHref(node.node_code)} key={node.node_code}>
                      <span>{koCode(node.cycle_state)} · {formatPercent(node.cycle_score)}</span>
                      <strong>{koCode(node.node_code)}</strong>
                      <small>{nodeQuestion(node)}</small>
                      <b>뉴스 {node.counts.direct_event_count} · 전파 {node.counts.propagated_impact_count}</b>
                    </Link>
                  ))}
              </div>
            </section>
          ))}
        </div>
      </section>

      <section className="cycle-path-workbench reveal delay-3" id="cycle-map-layers" aria-label="계층형 사이클 판단 경로">
        {groups.length === 0 ? (
          <article className="empty-state">
            아직 표시할 계층형 사이클 스냅샷이 없다. 뉴스 근거, 상위 흐름 영향, 사이클 상태가 쌓이면 거시→섹터→테마→종목 경로로 표시된다.
          </article>
        ) : null}

        <div className="section-heading stacked-heading">
          <span>판단 경로</span>
          <h2>흐름이 종목과 추천으로 내려가는 길을 한 줄씩 확인한다</h2>
          <p>
            각 행은 원인을 단정하지 않는다. 상위 흐름과 종목 노출이 같은 방향인지 확인하는 추적 경로다.
            추천 점수와 실거래 경계는 추천 상세와 거래 안전 화면에서 별도로 확인한다.
          </p>
        </div>

        <div className="cycle-path-table">
          {pathNodes.map((node) => (
            <article className={`cycle-path-row ${nodeTone(node)}`} key={`path-${node.node_code}`}>
              <div className="cycle-path-cell">
                <span>상위 흐름</span>
                <strong>{nodeDriverText(node)}</strong>
                <small>{node.recent_event_titles[0] ? koLabel(node.recent_event_titles[0]) : "최근 뉴스 원천은 뉴스 근거 화면에서 확인한다."}</small>
              </div>
              <div className="cycle-path-cell emphasis">
                <span>현재 사이클</span>
                <strong>{koCode(node.node_code)}</strong>
                <small>{koCode(node.cycle_state)} · 점수 {formatPercent(node.cycle_score)} · {nodeEvidenceLine(node)}</small>
              </div>
              <div className="cycle-path-cell">
                <span>내려가는 대상</span>
                <strong>{nodeDownstreamText(node)}</strong>
                <small>하위 흐름 {node.child_codes.length}개 · 노출 종목 {node.counts.exposed_instrument_count}개</small>
              </div>
              <div className="cycle-path-cell action">
                <span>다음 확인</span>
                <strong>{nodeDecisionLabel(node)}</strong>
                <small>{nodeNextAction(node)}</small>
                <div className="cycle-path-actions">
                  <Link className="btn btn-primary" href={nodeHref(node.node_code)}>
                    흐름 상세
                  </Link>
                  {node.top_symbols[0] ? (
                    <Link className="btn btn-secondary" href={stockHref(node.top_symbols[0])}>
                      {koCode(node.top_symbols[0])}
                    </Link>
                  ) : (
                    <Link className="btn btn-secondary" href={"/intelligence" as Route}>
                      뉴스 근거
                    </Link>
                  )}
                </div>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="bento-card reveal delay-3" aria-label="흐름 관계">
        <div className="section-heading stacked-heading">
          <span>관계선</span>
          <h2>상위 흐름이 아래 흐름으로 이어지는 규칙</h2>
          <p>관계선은 사전에 정한 시장 분류 지도다. 거시 흐름이 어느 도메인·테마·종목으로 내려갈 수 있는지 확인한다.</p>
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
