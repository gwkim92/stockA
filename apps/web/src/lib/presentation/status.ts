export const DISPLAY_STATUS_KINDS = [
  "ready",
  "watch",
  "stale",
  "source_limited",
  "blocked",
  "not_applicable",
  "empty",
  "error",
] as const;

export type DisplayStatusKind = (typeof DISPLAY_STATUS_KINDS)[number];

export type DisplayStatus = {
  readonly kind: DisplayStatusKind;
  readonly label: string;
  readonly description: string;
};

type DataCondition = {
  readonly blocked?: boolean;
  readonly failed?: boolean;
  readonly sourceLimited?: boolean;
  readonly stale?: boolean;
  readonly empty?: boolean;
  readonly notApplicable?: boolean;
  readonly watch?: boolean;
};

const STATUS_COPY: Readonly<Record<DisplayStatusKind, Omit<DisplayStatus, "kind">>> = {
  ready: {
    label: "정상",
    description: "현재 판단에 사용할 수 있는 상태다.",
  },
  watch: {
    label: "관찰",
    description: "방향은 보이지만 추가 근거가 필요하다.",
  },
  stale: {
    label: "오래됨",
    description: "최신성이 낮아 현재 판단에 주의가 필요하다.",
  },
  source_limited: {
    label: "원천 제한",
    description: "필요한 원천 자료가 부족해 해석 범위가 제한된다.",
  },
  blocked: {
    label: "안전 차단",
    description: "오류가 아니라 안전 규칙이 다음 행동을 막고 있다.",
  },
  not_applicable: {
    label: "해당 없음",
    description: "이 대상에는 해당 분석 기준을 적용하지 않는다.",
  },
  empty: {
    label: "데이터 없음",
    description: "현재 표시할 데이터가 아직 없다.",
  },
  error: {
    label: "오류",
    description: "작업 실패로 현재 결과를 신뢰할 수 없다.",
  },
};

export function displayStatus(kind: DisplayStatusKind): DisplayStatus {
  return {
    kind,
    ...STATUS_COPY[kind],
  };
}

export function statusFromDataCondition(condition: DataCondition): DisplayStatusKind {
  if (condition.failed) {
    return "error";
  }
  if (condition.blocked) {
    return "blocked";
  }
  if (condition.sourceLimited) {
    return "source_limited";
  }
  if (condition.stale) {
    return "stale";
  }
  if (condition.notApplicable) {
    return "not_applicable";
  }
  if (condition.empty) {
    return "empty";
  }
  if (condition.watch) {
    return "watch";
  }
  return "ready";
}
