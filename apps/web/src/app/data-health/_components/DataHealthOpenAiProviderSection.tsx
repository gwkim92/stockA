import {
  aiProviderLabel,
  formatUsdAmount,
  openAiProviderExplanation,
  openAiProviderTitle,
  openAiProviderTone,
  operationCopy,
  optionalTimestamp,
} from "./dataHealthModel";
import type { OpenAiProviderHealth } from "./dataHealthTypes";

type DataHealthOpenAiProviderSectionProps = {
  readonly openAiProviderHealth: OpenAiProviderHealth;
};

export function DataHealthOpenAiProviderSection({
  openAiProviderHealth,
}: DataHealthOpenAiProviderSectionProps) {
  return (
    <section
      className="feature-map-panel reveal delay-1"
      id="openai-provider-health"
      aria-labelledby="openai-provider-health-title"
    >
      <div className="section-heading stacked-heading">
        <span>OpenAI 잔액·쿼터 상태</span>
        <h2 id="openai-provider-health-title">
          OpenAI API를 바로 쓸 수 있는지와 중단 시 어떤 경로로 우회하는지 본다.
        </h2>
      </div>
      <p className="board-intro">{openAiProviderExplanation(openAiProviderHealth)}</p>
      <div className="status-rail compact-rail">
        <article className="rail-cell">
          <span>판정</span>
          <strong className={`risk-tag ${openAiProviderTone(openAiProviderHealth)}`}>
            {openAiProviderTitle(openAiProviderHealth)}
          </strong>
          <small>{operationCopy(openAiProviderHealth.status)}</small>
        </article>
        <article className="rail-cell">
          <span>남은 잔액</span>
          <strong>
            {openAiProviderHealth.remaining_balance_usd === null
              ? "공식 API 없음"
              : `$${openAiProviderHealth.remaining_balance_usd.toFixed(2)}`}
          </strong>
          <small>실제 잔액은 Billing Overview에서 확인</small>
        </article>
        <article className="rail-cell">
          <span>최근 비용</span>
          <strong>{formatUsdAmount(openAiProviderHealth.cost_status.total_cost_usd)}</strong>
          <small>
            최근 {openAiProviderHealth.cost_status.lookback_days}일 ·{" "}
            {operationCopy(openAiProviderHealth.cost_status.status)}
          </small>
        </article>
        <article className="rail-cell">
          <span>최근 1일 비용</span>
          <strong>{formatUsdAmount(openAiProviderHealth.cost_status.latest_day_cost_usd)}</strong>
          <small>
            {openAiProviderHealth.cost_status.period_start || "기간 미확인"} →{" "}
            {openAiProviderHealth.cost_status.period_end || "기간 미확인"}
          </small>
        </article>
        <article className="rail-cell">
          <span>다음 재시도</span>
          <strong>{optionalTimestamp(openAiProviderHealth.next_retry_at)}</strong>
          <small>마지막 확인 {optionalTimestamp(openAiProviderHealth.last_checked_at)}</small>
        </article>
        <article className="rail-cell">
          <span>우회 경로</span>
          <strong>{aiProviderLabel(openAiProviderHealth.fallback_provider)}</strong>
          <small>최종 대체 {aiProviderLabel(openAiProviderHealth.local_fallback_provider)}</small>
        </article>
        <article className="rail-cell">
          <span>Admin 비용 API</span>
          <strong>{openAiProviderHealth.admin_api_key_configured ? "설정됨" : "없음"}</strong>
          <small>{operationCopy(openAiProviderHealth.cost_status.message)}</small>
        </article>
      </div>
      <div className="empty-state">
        <strong>분기 원칙</strong>
        <p>
          화면 요청에서는 OpenAI를 호출하지 않습니다. 배치 작업에서 중단이 감지되면 AI 상태 기록에
          남기고, 만료 전까지 OpenAI 직접 호출을 건너뛰어{" "}
          {aiProviderLabel(openAiProviderHealth.fallback_provider)} 또는{" "}
          {aiProviderLabel(openAiProviderHealth.local_fallback_provider)}로 내려간다.
        </p>
        <p>
          Admin Costs API는 사용 비용만 제공한다. 잔액 자체는{" "}
          <a href={openAiProviderHealth.cost_status.billing_overview_url}>OpenAI Billing Overview</a>에서 직접
          본다.
        </p>
      </div>
    </section>
  );
}
