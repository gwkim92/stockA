import { koCode } from "@/lib/korean-labels";

import {
  aiInvocationErrorCopy,
  liveAiCurrentFailureCount,
  liveAiCurrentFailureDetail,
  liveAiInvocationExplanation,
  liveAiInvocationHistoryLabel,
  liveAiInvocationTitle,
  liveAiInvocationTone,
  operationCopy,
} from "./dataHealthModel";
import type { LiveAiInvocationHealth } from "./dataHealthTypes";

type DataHealthLiveAiInvocationSectionProps = {
  readonly liveAiInvocationHealth: LiveAiInvocationHealth;
};

export function DataHealthLiveAiInvocationSection({
  liveAiInvocationHealth,
}: DataHealthLiveAiInvocationSectionProps) {
  return (
    <section
      className="feature-map-panel reveal delay-1"
      id="live-ai-invocation-health"
      aria-labelledby="live-ai-invocation-health-title"
    >
      <div className="section-heading stacked-heading">
        <span>실제 AI 호출 상태</span>
        <h2 id="live-ai-invocation-health-title">
          기준 세트 통과와 별개로, {"운영\u00a0배치가"} 실제 AI를 호출했는지 본다.
        </h2>
      </div>
      <p className="board-intro">{liveAiInvocationExplanation(liveAiInvocationHealth)}</p>
      <div className="status-rail compact-rail">
        <article className="rail-cell">
          <span>판정</span>
          <strong className={`risk-tag ${liveAiInvocationTone(liveAiInvocationHealth)}`}>
            {liveAiInvocationTitle(liveAiInvocationHealth)}
          </strong>
          <small>최근 {liveAiInvocationHealth.window_hours}시간</small>
        </article>
        <article className="rail-cell">
          <span>최근 호출</span>
          <strong>{liveAiInvocationHealth.recent_invocation_count}</strong>
          <small>{liveAiInvocationHistoryLabel(liveAiInvocationHealth)}</small>
        </article>
        <article className="rail-cell">
          <span>현재 중단 작업</span>
          <strong>{liveAiCurrentFailureCount(liveAiInvocationHealth)}</strong>
          <small>{liveAiCurrentFailureDetail(liveAiInvocationHealth)}</small>
        </article>
        <article className="rail-cell">
          <span>최신 중단 작업</span>
          <strong>{koCode(liveAiInvocationHealth.latest_failed_task_name) || "없음"}</strong>
          <small>{liveAiInvocationHealth.latest_failed_at || "최근 중단 없음"}</small>
        </article>
      </div>
      <div className="simple-table-wrap">
        <table className="simple-table">
          <thead>
            <tr>
              <th>작업</th>
              <th>최근 상태</th>
              <th>성공/중단</th>
              <th>최신 오류</th>
            </tr>
          </thead>
          <tbody>
            {liveAiInvocationHealth.task_health.map((task) => (
              <tr key={task.task_name}>
                <td>
                  <strong>{task.label || koCode(task.task_name)}</strong>
                  <small>{task.critical ? "핵심 AI 작업" : "보조 AI 작업"}</small>
                </td>
                <td>{koCode(task.latest_status)}</td>
                <td>{task.recent_success_count}/{task.recent_failed_count}</td>
                <td>
                  {task.latest_error_summary
                    ? aiInvocationErrorCopy(task.latest_error_summary, task.latest_error_code)
                    : task.latest_created_at || "최근 호출 없음"}
                </td>
              </tr>
            ))}
            {liveAiInvocationHealth.task_health.length === 0 ? (
              <tr>
                <td colSpan={4}>최근 실제 AI 호출 기록이 없다.</td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>
      <div className="empty-state">
        <strong>다음 조치</strong>
        <p>{operationCopy(liveAiInvocationHealth.next_action)}</p>
        <p>
          Codex OAuth 연결 상태는{" "}
          <a className="text-link" href="/admin/ai-agents#codex-oauth-operator">
            AI 운영 상태 화면
          </a>
          에서 읽기 전용으로 확인합니다. 재로그인과 {"실제\u00a0AI\u00a0호출\u00a0점검"}은 서버 CLI/SSH에서만
          실행합니다.
        </p>
      </div>
    </section>
  );
}
