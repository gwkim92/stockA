export type ResearchRefreshRow = {
  symbol: string;
  state: string;
  source_run_id: number | null;
  source_collected_at: string | null;
  claim_id: number | null;
  retry_after: string | null;
  failure_code: string | null;
};
export type ResearchRefreshStatus = {
  status: "loaded" | "attention_required" | "unavailable";
  observed_at: string;
  as_of_date: string;
  budget_resets_at: string;
  model_name: string | null;
  daily_used: number | null;
  daily_limit: number | null;
  daily_remaining: number | null;
  total_count: number | null;
  attention_count: number | null;
  counts: Record<string, number>;
  rows: ResearchRefreshRow[];
};

export const refreshStates: Record<string, { label: string; detail: string; attention?: boolean }> = {
  current: { label: "재무 버전 일치", detail: "현재 재무 자료로 생성된 보고서와 저장 결과를 확인했습니다." },
  due: { label: "생성 대기", detail: "재무 자료 또는 생성 설정이 바뀌었습니다. 다음 자동 실행에서 순서대로 처리합니다." },
  waiting_for_source: { label: "원천 자료 대기", detail: "지원하는 재무 자료의 수집 성공 기록이 필요합니다. 정기 수집 결과를 기다립니다." },
  retry_wait: { label: "재시도 대기", detail: "AI 생성 실패 후 대체 보고서가 저장됐습니다. 24시간 뒤 한도 안에서 재시도합니다." },
  reconcile: { label: "실행 결과 확인 중", detail: "실행 중이거나 저장 결과가 확정되지 않았습니다. 중복 호출을 막고 저장 기록을 대조합니다.", attention: true },
  attempt_recorded: { label: "실패 확인 필요", detail: "완료된 생성 결과를 확인하지 못했습니다. 기록을 확인할 때까지 자동 재호출하지 않습니다.", attention: true },
  result_changed: { label: "저장 결과 확인 필요", detail: "완료 기록과 현재 저장된 결과가 다릅니다. 자동 재호출을 멈추고 기록을 확인합니다.", attention: true },
  unknown: { label: "상태 확인 필요", detail: "현재 상태를 판정하지 못했습니다.", attention: true },
};

export function refreshTime(value: string | null | undefined): string {
  if (!value) return "기록 없음";
  const date = new Date(value);
  if (!Number.isFinite(date.getTime())) return "기록 없음";
  return new Intl.DateTimeFormat("ko-KR", { timeZone: "Asia/Seoul", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", hour12: false }).format(date);
}
