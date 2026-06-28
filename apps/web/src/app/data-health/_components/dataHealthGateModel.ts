import type { GateTriageBucket, OpenGateDetail } from "./dataHealthTypes";

import { gateSeverityTone } from "./dataHealthCopyModel";

export function gateTriageKey(gate: OpenGateDetail) {
  const text = `${gate.gate_id} ${gate.category} ${gate.label} ${gate.summary} ${gate.next_action}`.toLowerCase();
  if (gate.category === "outcome_due") {
    return "due-now";
  }
  if (text.includes("outcome") || text.includes("성과") || text.includes("wait")) {
    return "managed-wait";
  }
  if (gate.category === "source_limit" || text.includes("source") || text.includes("원천")) {
    return "source-limit";
  }
  if (
    gate.category === "investment_review"
    || text.includes("benchmark")
    || text.includes("portfolio")
    || text.includes("벤치마크")
    || text.includes("포트폴리오")
  ) {
    return "investment-review";
  }
  if (gate.severity === "high") {
    return "fix-now";
  }
  return "watch";
}

export const GATE_TRIAGE_BUCKETS: Omit<GateTriageBucket, "gates">[] = [
  {
    key: "fix-now",
    label: "즉시 조치",
    title: "수집·AI·접근 장애",
    description: "서비스 신뢰도를 직접 낮추는 항목이다. 추천 화면을 보기 전에 먼저 닫는다.",
    tone: "risk-high",
    href: "#runtime-boundary",
  },
  {
    key: "due-now",
    label: "실행 기한",
    title: "성과·검토 실행 필요",
    description: "성과창이 열렸거나 사후평가 실행 조건이 충족됐다. 자동 주문 없이 검증 작업만 실행한다.",
    tone: "risk-medium",
    href: "#outcome-maturity-wait-monitor",
  },
  {
    key: "managed-wait",
    label: "관리된 대기",
    title: "성과 측정일까지 기다림",
    description: "문제가 아니라 설계된 대기다. 표본이 성숙하기 전까지 추천 산식 변경을 막는다.",
    tone: "risk-medium",
    href: "#outcome-maturity-wait-monitor",
  },
  {
    key: "source-limit",
    label: "원천 한계",
    title: "원천 데이터 부족",
    description: "합성 재무를 만들지 않고 전문 판단·가상 매매 입력에서 제외한 항목이다.",
    tone: "risk-medium",
    href: "#professional-source-gaps",
  },
  {
    key: "investment-review",
    label: "투자 검토",
    title: "포트폴리오·벤치마크 확인",
    description: "자동 주문이 아니라 검토 기록과 사후 성과 대조가 필요한 항목이다.",
    tone: "risk-medium",
    href: "#investment-quality-details",
  },
  {
    key: "watch",
    label: "관찰",
    title: "관찰 중인 항목",
    description: "즉시 장애는 아니지만 다음 배치와 최신 실행 기록을 계속 본다.",
    tone: "risk-low",
    href: "#execution-log",
  },
];

export function buildGateTriageBuckets(gates: OpenGateDetail[]) {
  const buckets = GATE_TRIAGE_BUCKETS.map((bucket) => ({ ...bucket, gates: [] as OpenGateDetail[] }));
  for (const gate of gates) {
    const key = gateTriageKey(gate);
    const bucket = buckets.find((candidate) => candidate.key === key) ?? buckets[buckets.length - 1];
    bucket.gates.push(gate);
  }
  return buckets;
}

export function gateTriageSummary(buckets: GateTriageBucket[], rawOpenGateCount: number) {
  const fixNowCount = buckets.find((bucket) => bucket.key === "fix-now")?.gates.length ?? 0;
  const dueNowCount = buckets.find((bucket) => bucket.key === "due-now")?.gates.length ?? 0;
  const managedWaitCount = buckets.find((bucket) => bucket.key === "managed-wait")?.gates.length ?? 0;
  const sourceLimitCount = buckets.find((bucket) => bucket.key === "source-limit")?.gates.length ?? 0;
  if (fixNowCount > 0) {
    return `즉시 조치 ${fixNowCount}개가 있다. 수집·AI·접근 장애를 먼저 닫아야 한다.`;
  }
  if (dueNowCount > 0) {
    return `성과 실행 기한이 된 항목 ${dueNowCount}개가 있다. 주문 없이 검증·성과 산출 작업만 실행한다.`;
  }
  if (sourceLimitCount > 0) {
    return `열린 항목 ${rawOpenGateCount}개 중 핵심은 원천 한계다. 합성 재무를 만들지 않고 판단 입력에서 차단한 상태다.`;
  }
  if (managedWaitCount > 0) {
    return `열린 항목 ${rawOpenGateCount}개는 대부분 성과 측정일까지 기다리는 관리된 대기다.`;
  }
  if (rawOpenGateCount > 0) {
    return `열린 항목 ${rawOpenGateCount}개가 있다. 아래 분류에서 조치 위치를 나눈다.`;
  }
  return "현재 열린 항목은 없다. 세부 실행 이력과 최신성만 필요할 때 보면 된다.";
}
