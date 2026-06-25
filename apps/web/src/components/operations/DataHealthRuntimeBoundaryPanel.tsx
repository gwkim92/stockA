import type { DataHealthRuntimeBoundaryPanel as DataHealthRuntimeBoundaryPanelData } from "./DataHealthRuntimeDetailPanelTypes";

type DataHealthRuntimeBoundaryPanelProps = {
  readonly panel: DataHealthRuntimeBoundaryPanelData;
};

const runtimeRows = [
  ["읽기 서버", "apiReadinessLabel"],
  ["데이터 연결", "connectionLabel"],
  ["읽기 보호", "readProtectionLabel"],
  ["조회 권한", "authReadinessLabel"],
  ["읽기 범위", "readScopeLabel"],
  ["주문/쓰기 차단", "brokerOrderLabel"],
  ["권한 다음 조치", "authNextActionLabel"],
  ["API 다음 조치", "apiNextActionLabel"],
  ["알림 목적지", "notificationReadinessLabel"],
  ["알림 방식", "notificationMethodLabel"],
  ["알림 다음 조치", "notificationNextActionLabel"],
  ["자동 실행기", "schedulerReadinessLabel"],
  ["환경", "environmentLabel"],
  ["승인 상태", "schedulerEnvironmentLabel"],
  ["대상 작업", "schedulerJobLabel"],
  ["승인 조건", "schedulerApprovalGateLabel"],
  ["활성화 가능", "schedulerActivationAllowedLabel"],
  ["다음 단계", "schedulerNextStepLabel"],
  ["휴장일 처리", "holidaySkipModeLabel"],
  ["실행 증거", "artifactEvidenceLabel"],
  ["저장 정책", "artifactPolicyLabel"],
  ["실행 증거 경로", "artifactLatestRootLabel"],
  ["실행 증거 다음 조치", "artifactNextActionLabel"],
] as const;

export function DataHealthRuntimeBoundaryPanel({ panel }: DataHealthRuntimeBoundaryPanelProps) {
  return (
    <article className="ledger-panel">
      <div className="section-heading stacked-heading">
        <span>자동 반복 실행</span>
        <h2>반복 실행 준비 상태</h2>
      </div>
      <dl className="fact-list">
        {runtimeRows.map(([label, field]) => (
          <div key={field}>
            <dt>{label}</dt>
            <dd>{panel[field]}</dd>
          </div>
        ))}
      </dl>
    </article>
  );
}
