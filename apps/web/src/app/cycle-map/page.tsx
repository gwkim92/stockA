import Link from "next/link";
import type { Route } from "next";

import { DecisionSummary } from "@/components/research/DecisionSummary";
import { MetricStrip } from "@/components/research/MetricStrip";
import { getCycleMap, getCycleStates } from "@/lib/frontend-api";
import { koCode } from "@/lib/korean-labels";
import type { CycleMapData, CycleStateListData } from "@/lib/types";
import {
  cycleAttentionScore,
  cycleStateForNode,
  cycleText,
  flowPathText,
  formatCount,
  formatPercent,
  groupedNodes,
  levelTitle,
  nodeDecisionLabel,
  nodeDownstreamText,
  nodeDriverText,
  nodeEvidenceLine,
  nodeHref,
  nodeNextAction,
  nodeQuestion,
  nodeSummary,
  nodeTone,
  shortText,
  stockHref,
  topNodeLabel,
} from "./_components/cycleMapModel";
import { CycleImpactPathSection } from "./_components/CycleImpactPathSection";

export const dynamic = "force-dynamic";
export const metadata = { title: "흐름 지도" };

type CycleNode = CycleMapData["nodes"][number];
type CycleState = CycleStateListData["cycle_states"][number];

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
      <DecisionSummary
        eyebrow={`사이클 지도 · ${data.as_of_date}`}
        title={`${topNodeLabel(hotNode)} 흐름이 현재 시장을 주도합니다.`}
        description="거시 변화가 산업·테마·종목으로 번지는 경로와 충돌 신호를 함께 봅니다."
        primaryAction={{
          href: hotNode ? nodeHref(hotNode.node_code) : ("/intelligence" as Route),
          label: hotNode ? "주도 흐름 분석" : "뉴스 근거 보기",
        }}
        secondaryActions={[
          { href: "/intelligence" as Route, label: "뉴스 근거" },
          { href: "/cycles" as Route, label: "사이클 상태표" },
        ]}
        side={
          <div className="research-lead-snapshot">
            <span>주도 사이클</span>
            <strong>{topNodeLabel(hotNode)}</strong>
            <small>
              뉴스 영향 {hotNode?.counts.direct_event_count ?? 0}개 · 종목 연결 {hotNode?.counts.exposed_instrument_count ?? 0}개
            </small>
          </div>
        }
      />
      <MetricStrip
        label="사이클 지도 현황"
        items={[
          { label: "추적 흐름", value: `${data.summary.node_count}개`, context: `거시 ${data.summary.macro_count} · 테마 ${data.summary.theme_count}` },
          { label: "뉴스 영향", value: `${data.summary.direct_event_count}개`, context: `AI 근거 연결 ${aiBackedNodeCount}개 흐름` },
          { label: "종목 연결", value: `${exposedNodeCount}개`, context: `연결 대기 ${symbolGapCount}개` },
          { label: "충돌 신호", value: `${conflictNodeCount}개`, context: conflictNodeCount > 0 ? "상위·하위 흐름 불일치" : "뚜렷한 충돌 없음" },
          { label: "추천 영향", value: `${data.summary.recommendation_count}개`, context: "추천 상세에서 근거 확인" },
        ]}
      />

      <section className="cycle-operating-board" aria-labelledby="cycle-operating-title">
        <div className="cycle-attention-panel">
          <div className="section-heading stacked-heading">
            <span>주도 사이클</span>
            <h2 id="cycle-operating-title">시장 영향력이 큰 흐름</h2>
            <p>뉴스 강도, 사이클 상태, 하위 전파, 추천 영향, 충돌 신호를 합산한 순위입니다.</p>
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

        <aside className="cycle-command-aside" aria-label="사이클 변화 요약">
          <article className="cycle-playbook">
            <span>상태 전환</span>
            <strong>{turningCycles.length.toLocaleString("ko-KR")}개 변화</strong>
            <p>{turningCycles.length > 0 ? turningCycles.map((cycle) => koCode(cycle.theme_key)).join(" · ") : "현재 상태가 바뀐 사이클은 없습니다."}</p>
          </article>
          <article className="cycle-playbook">
            <span>뉴스 강도 상위</span>
            <strong>{eventLedCycles.length.toLocaleString("ko-KR")}개 흐름</strong>
            <p>{eventLedCycles.map((cycle) => koCode(cycle.theme_key)).join(" · ")}</p>
          </article>
          <article className="cycle-playbook warning">
            <span>근거 제한</span>
            <strong>{evidenceGapCount.toLocaleString("ko-KR")}개 · 종목 연결 대기 {symbolGapCount.toLocaleString("ko-KR")}개</strong>
            <p>가격, 뉴스 또는 종목 노출이 부족한 흐름은 확정 신호가 아닌 관찰 상태로 유지됩니다.</p>
          </article>
        </aside>
      </section>

      <section className="cycle-lane-board" aria-labelledby="cycle-lane-title">
        <div className="section-heading stacked-heading">
          <span>계층 지도</span>
          <h2 id="cycle-lane-title">거시에서 종목까지 이어지는 현재 위치</h2>
          <p>각 단계의 상태와 강도를 비교해 상위 환경과 종목 흐름이 같은 방향인지 확인합니다.</p>
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

      <CycleImpactPathSection groups={groups} pathNodes={pathNodes} />

      <section className="bento-card" aria-label="흐름 관계">
        <div className="section-heading stacked-heading">
          <span>관계선</span>
          <h2>상위 흐름이 <span className="keep-phrase">아래 흐름</span>으로 이어지는 규칙</h2>
          <p>관계선은 사전에 정한 시장 분류 지도입니다. 상위 흐름과 연결된 하위 대상을 보여줍니다.</p>
        </div>
        {data.edges.length > 0 ? (
          <div className="relationship-list">
            {data.edges.slice(0, 24).map((edge) => (
              <div className="relationship-chip" key={`${edge.parent_code}-${edge.child_code}-${edge.relation_type}`}>
                <span>{koCode(edge.relation_type)} · {formatPercent(edge.weight)}</span>
                <strong>{koCode(edge.parent_code)} → {koCode(edge.child_code)}</strong>
                <small>{koCode(edge.parent_code)} → {koCode(edge.child_code)} 연결 경로</small>
              </div>
            ))}
          </div>
        ) : (
          <div className="empty-state">현재 기준일에 표시할 흐름 관계가 없습니다.</div>
        )}
      </section>
    </div>
  );
}
