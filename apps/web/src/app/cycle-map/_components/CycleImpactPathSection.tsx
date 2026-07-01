import Link from "next/link";
import type { Route } from "next";

import { koCode } from "@/lib/korean-labels";
import type { CycleMapData } from "@/lib/types";
import {
  cycleText,
  formatPercent,
  nodeDecisionLabel,
  nodeDownstreamText,
  nodeDriverText,
  nodeEvidenceLine,
  nodeHref,
  nodeNextAction,
  nodeTone,
  stockHref,
} from "./cycleMapModel";

type CycleNode = CycleMapData["nodes"][number];
type CycleGroup = {
  readonly level: string;
  readonly title: string;
  readonly nodes: readonly CycleNode[];
};

export function CycleImpactPathSection({
  groups,
  pathNodes,
}: {
  readonly groups: readonly CycleGroup[];
  readonly pathNodes: readonly CycleNode[];
}) {
  return (
    <section className="cycle-path-workbench reveal delay-3" id="cycle-map-layers" aria-label="계층형 사이클 판단 경로">
      {groups.length === 0 ? (
        <article className="empty-state">
          아직 표시할 계층형 사이클 스냅샷이 없습니다. 뉴스 근거, 상위 흐름 영향, 사이클 상태가 쌓이면 거시→섹터→테마→종목 경로로 표시됩니다.
        </article>
      ) : null}

      <div className="section-heading stacked-heading">
        <span>영향 경로</span>
        <h2>상위 흐름이 종목과 추천에 미친 영향</h2>
        <p>상위 흐름과 종목 노출이 같은 방향인지 비교합니다. 원인과 결과를 단정하지 않고 근거 강도를 함께 표시합니다.</p>
      </div>

      <div className="cycle-path-table">
        {pathNodes.map((node) => (
          <article className={`cycle-path-row ${nodeTone(node)}`} key={`path-${node.node_code}`}>
            <div className="cycle-path-cell">
              <span>상위 흐름</span>
              <strong>{nodeDriverText(node)}</strong>
              <small>{cycleText(node.recent_event_titles[0], "최근 뉴스 원천은 뉴스 근거 화면에서 확인할 수 있습니다.")}</small>
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
  );
}
