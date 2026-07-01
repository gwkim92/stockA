import type { Route } from "next";

import { koCode, koLabel } from "@/lib/korean-labels";
import type { CycleMapData, CycleStateListData } from "@/lib/types";

type CycleNode = CycleMapData["nodes"][number];
type CycleState = CycleStateListData["cycle_states"][number];

const LEVEL_ORDER = ["macro", "domain", "sector", "theme", "instrument", "unknown"] as const;
const HIGH_EVENT_THRESHOLD = 0.55;
const HIGH_SCORE_THRESHOLD = 0.6;

export function formatPercent(value: number | null | undefined) {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return "미측정";
  }
  return `${Math.round(value * 1000) / 10}%`;
}

export function levelTitle(level: string) {
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

export function nodeHref(nodeCode: string) {
  return `/themes/${encodeURIComponent(nodeCode)}` as Route;
}

export function stockHref(symbol: string) {
  return `/stocks/${encodeURIComponent(symbol)}` as Route;
}

function nodeHeat(node: CycleNode) {
  return node.event_heat_score ?? node.cycle_score ?? 0;
}

export function formatCount(value: number) {
  return value.toLocaleString("ko-KR");
}

export function shortText(value: string | null | undefined, fallback: string) {
  const text = cycleInvestorText(value || fallback);
  return text.length > 140 ? `${text.slice(0, 140)}...` : text;
}

export function cycleText(value: string | null | undefined, fallback: string) {
  return cycleInvestorText(value || fallback);
}

function cycleInvestorText(value: string) {
  return koLabel(value)
    .replace(/\bbreadth_score\b/g, "시장 참여도 점수")
    .replace(/\bprice_momentum\b/g, "가격 모멘텀")
    .replace(/\bevent_intensity\b/g, "뉴스 강도")
    .replace(/\bfundamental_quality\b/g, "펀더멘털 신뢰도")
    .replace(/\bcycle_score\b/g, "사이클 점수")
    .replace(/\bTECHNOLOGY\b/g, "기술 섹터")
    .replace(/\bsubtheme\b/gi, "하위 테마")
    .replace(/\bcooling\b/gi, "열기 둔화")
    .replace(/\bcommunity\b/gi, "흐름")
    .replace(/\bmissing\b/gi, "데이터 대기")
    .replace(/\bwait\b/gi, "대기")
    .replace(/점검해야 한다/g, "점검 대상입니다")
    .replace(/확인해야 한다/g, "확인 대상입니다")
    .replace(/기다린다/g, "대기합니다")
    .trim();
}

export function cycleAttentionScore(node: CycleNode) {
  const heat = node.event_heat_score ?? 0;
  const cycleScore = node.cycle_score ?? 0;
  const propagation = Math.min(1, node.counts.propagated_impact_count / 80);
  const recommendations = Math.min(1, node.counts.recommendation_count / 20);
  const conflicts = node.conflict_flags.length > 0 ? 0.22 : 0;
  return heat * 0.34 + cycleScore * 0.22 + propagation * 0.2 + recommendations * 0.14 + conflicts;
}

export function nodeTone(node: CycleNode) {
  if (node.conflict_flags.length > 0) {
    return "tone-watch";
  }
  if ((node.cycle_score ?? 0) >= HIGH_SCORE_THRESHOLD || nodeHeat(node) >= HIGH_EVENT_THRESHOLD) {
    return "tone-ready";
  }
  return "tone-neutral";
}

export function nodeDecisionLabel(node: CycleNode) {
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

export function topNodeLabel(node: CycleNode | null) {
  return node ? koCode(node.node_code) : "사이클 데이터 대기";
}

export function nodeQuestion(node: CycleNode) {
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

export function nodeDriverText(node: CycleNode) {
  if (node.parent_codes.length > 0) {
    return node.parent_codes.slice(0, 2).map(koCode).join(" · ");
  }
  return node.cycle_level === "macro" ? "거시 뉴스와 시장 지표" : `${levelTitle(node.cycle_level)} 자체 흐름`;
}

export function nodeDownstreamText(node: CycleNode) {
  if (node.child_codes.length > 0) {
    return node.child_codes.slice(0, 2).map(koCode).join(" · ");
  }
  if (node.top_symbols.length > 0) {
    return node.top_symbols.slice(0, 3).map(koCode).join(" · ");
  }
  return "아직 하위 노출 대기";
}

export function nodeEvidenceLine(node: CycleNode) {
  return `뉴스 ${formatCount(node.counts.direct_event_count)} · 전파 ${formatCount(node.counts.propagated_impact_count)} · 추천 ${formatCount(node.counts.recommendation_count)}`;
}

export function nodeNextAction(node: CycleNode) {
  if (node.counts.recommendation_count > 0) {
    return "이 흐름이 추천 점수와 근거에 미친 영향을 확인할 수 있습니다.";
  }
  if (node.top_symbols.length > 0) {
    return "대표 종목의 직접 뉴스, 상위 흐름과 시장 동조성이 연결됩니다.";
  }
  if (node.counts.direct_event_count > 0) {
    return "원천 뉴스와 종목·테마 영향이 뉴스 근거 화면에 연결됩니다.";
  }
  return "다음 뉴스/가격 수집 후 상태 변화가 표시됩니다.";
}

export function flowPathText(data: CycleMapData, node: CycleNode) {
  const parent = data.edges.find((edge) => edge.child_code === node.node_code)?.parent_code;
  const child = data.edges.find((edge) => edge.parent_code === node.node_code)?.child_code;
  return [parent, node.node_code, child].filter(Boolean).map(koCode).join(" → ");
}

export function cycleStateForNode(states: Map<string, CycleState>, node: CycleNode) {
  return states.get(node.node_code) ?? null;
}

export function nodeSummary(node: CycleNode) {
  const name = koCode(node.node_code);
  const state = koCode(node.cycle_state);
  return `${name}의 현재 상태는 ${state}입니다. 최근 뉴스 ${node.counts.direct_event_count}건, 상위 흐름 영향 ${node.counts.propagated_impact_count}건, 연결 종목 ${node.top_symbols.length}개, 추천 영향 ${node.counts.recommendation_count}건이 반영됐습니다.`;
}

export function groupedNodes(nodes: readonly CycleNode[]) {
  return LEVEL_ORDER.map((level) => ({
    level,
    title: levelTitle(level),
    nodes: nodes.filter((node) => node.cycle_level === level),
  })).filter((group) => group.nodes.length > 0);
}
