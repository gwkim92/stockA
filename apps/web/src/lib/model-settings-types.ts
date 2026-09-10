export type ModelInvocation = {
  id: string; task: string; started_at: number; finished_at: number | null;
  revision: number | null; requested_model: string; selected_model: string;
  actual_model: string | null; reasoning_effort: string | null;
  status: "running" | "succeeded" | "failed";
};
export type ModelSelection = { revision: number; default_model: string; overrides: Record<string, string> };
export type ModelSettings = ModelSelection & {
  enabled: boolean; authorized: boolean; session_expires_at: number | null;
  catalog: { id: string; label: string }[]; catalog_checked_at: number | null;
  history_available?: boolean;
  workloads: { task: string; label: string; purpose: string; source: string; execution: string;
    effective_model: string | null; latest: ModelInvocation | null; last_success: ModelInvocation | null;
    business_history?: { invocation_id: number; provider: string; model_name: string; status: string; created_at: string } | null }[];
  audit: { revision: number; changed_at: number; actor: string; before: ModelSelection; after: ModelSelection }[];
};
