import Link from "next/link";
import type { Route } from "next";

import { getAiAgentRegistry, getCodexOauthOperatorStatus } from "@/lib/frontend-api";
import type { AiAgentRegistryData, CodexOauthOperatorStatus } from "@/lib/types";
import CodexOauthOperatorPanel from "./CodexOauthOperatorPanel";

export const dynamic = "force-dynamic";
export const metadata = { title: "AI 에이전트 운영" };

type Agent = AiAgentRegistryData["agents"][number];

function providerLabel(provider: string) {
  if (provider === "agents_sdk_openai") {
    return "OpenAI Agents SDK";
  }
  if (provider === "codex_oauth") {
    return "Codex OAuth";
  }
  if (provider === "local_rules") {
    return "로컬 규칙";
  }
  return provider || "미지정";
}

function tierLabel(tier: string) {
  if (tier === "quality") {
    return "고품질";
  }
  if (tier === "balanced") {
    return "균형";
  }
  if (tier === "cheap") {
    return "저비용";
  }
  return tier || "미지정";
}

function domainLabel(domain: string) {
  const labels: Record<string, string> = {
    operations: "운영",
    news: "뉴스",
    ontology: "온톨로지",
    macro: "거시",
    cycle: "사이클",
    equity_research: "기업 분석",
    valuation: "밸류에이션",
    recommendation: "추천 검토",
    portfolio: "포트폴리오",
    paper_trading: "페이퍼 거래",
    data_quality: "데이터 품질",
    alerting: "알림",
  };
  return labels[domain] ?? domain;
}

function boundaryTone(agent: Agent) {
  if (agent.safety_boundary.can_trigger_order) {
    return "decision-card is-block";
  }
  if (agent.safety_boundary.can_write_canonical) {
    return "decision-card is-watch";
  }
  return "decision-card is-good";
}

function formatUsdCap(value: string) {
  const parsed = Number.parseFloat(value);
  if (!Number.isFinite(parsed)) {
    return value || "미지정";
  }
  if (parsed <= 0) {
    return "$0";
  }
  return `$${parsed.toFixed(2)}/일`;
}

function formatUsdAmount(value: number | null) {
  if (typeof value !== "number" || Number.isNaN(value)) {
    return "미조회";
  }
  return `$${value.toFixed(2)}`;
}

function providerSummary(data: AiAgentRegistryData) {
  return [
    `1차 ${data.primary_providers.map(providerLabel).join(", ") || "미지정"}`,
    `만료/실패 시 ${data.fallback_providers.map(providerLabel).join(", ") || "미지정"}`,
    `최종 대체 ${data.local_fallback_providers.map(providerLabel).join(", ") || "미지정"}`,
  ].join(" · ");
}

function runtimeStatusText(data: AiAgentRegistryData) {
  const health = data.runtime_policy.openai_provider_health;
  if (health.status === "openai_insufficient_quota" || health.status === "openai_billing_unavailable") {
    return `${health.message} 다음 OpenAI 재시도 시점까지는 ${providerLabel(health.fallback_provider)} 또는 ${providerLabel(health.local_fallback_provider)}를 사용한다.`;
  }
  if (data.runtime_policy.openai_api_disabled) {
    return "OpenAI API 호출은 운영 플래그로 꺼져 있다. 배치는 Codex OAuth 또는 로컬 규칙으로 내려가야 한다.";
  }
  if (data.runtime_policy.primary_provider_status === "known_billing_unavailable") {
    return "OpenAI API key는 있지만 잔액 또는 quota가 없는 상태로 표시돼 있다. 배치는 OpenAI를 건너뛰고 fallback을 사용해야 한다.";
  }
  if (data.runtime_policy.primary_provider_status === "costs_available_balance_not_returned") {
    return `OpenAI API key와 Admin key가 감지됐다. 최근 ${health.cost_status.lookback_days}일 비용은 ${formatUsdAmount(health.cost_status.total_cost_usd)}이고, 남은 잔액은 공식 Costs API가 반환하지 않아 Billing Overview에서 확인한다.`;
  }
  if (!data.runtime_policy.primary_api_key_configured) {
    return "OpenAI API 키는 이 요청 환경에서 감지되지 않았다. Codex OAuth 또는 로컬 규칙 fallback을 사용하도록 설계되어 있다.";
  }
  return "OpenAI API 키가 감지됐다. 실제 호출은 배치 작업에서만 수행하고 화면 요청 중에는 호출하지 않는다.";
}

function formatOptionalDate(value: string) {
  if (!value) {
    return "기록 없음";
  }
  return value.replace("T", " ").replace("+00:00", " UTC");
}

function defaultCodexOauthStatus(status: string): CodexOauthOperatorStatus {
  return {
    status: status || "unknown",
    label: status === "healthy" ? "정상" : status === "relogin_required" ? "재로그인 필요" : "미확인",
    summary: "Codex OAuth 운영 상태 endpoint가 아직 연결되지 않았다.",
    auth_url: "",
    user_code: "",
    expires_at: "",
    device_auth_pid: null,
    last_checked_at: "",
    last_event_type: "",
    last_smoke_status: "",
    last_smoke_at: "",
    last_error_code: "",
    last_error_summary: "",
    next_action: "Codex OAuth 운영 상태 endpoint와 admin action token 설정을 확인한다.",
    status_path: "",
    admin_action_required: true,
    read_only: true,
    broker_submit_allowed: false,
    automatic_order_allowed: false,
    order_boundary: "read_only_no_order",
  };
}

function AgentCard({ agent }: { agent: Agent }) {
  return (
    <article className={boundaryTone(agent)}>
      <span>{domainLabel(agent.owner_domain)}</span>
      <strong>{agent.display_name}</strong>
      <small>{agent.business_goal}</small>
      <dl className="runtime-grid">
        <div>
          <dt>1차 모델</dt>
          <dd>
            {providerLabel(agent.model_policy.primary_provider)} · {agent.model_policy.primary_model}
          </dd>
        </div>
        <div>
          <dt>Fallback</dt>
          <dd>
            {providerLabel(agent.model_policy.fallback_provider)} · {agent.model_policy.fallback_model}
          </dd>
        </div>
        <div>
          <dt>로컬 대체</dt>
          <dd>{providerLabel(agent.model_policy.local_fallback_provider)}</dd>
        </div>
        <div>
          <dt>프롬프트</dt>
          <dd>{agent.prompt_version}</dd>
        </div>
        <div>
          <dt>스키마</dt>
          <dd>{agent.output_schema_name}</dd>
        </div>
        <div>
          <dt>요청 한도</dt>
          <dd>
            {agent.model_policy.max_requests_per_run}회/run · {formatUsdCap(agent.model_policy.daily_usd_cap)}
          </dd>
        </div>
      </dl>
      <b>
        {agent.safety_boundary.can_trigger_order
          ? "주문 가능 경계 감지"
          : agent.safety_boundary.can_write_canonical
            ? "후보 작성만 허용"
            : "읽기 전용 · 주문 차단"}
      </b>
    </article>
  );
}

export default async function AiAgentAdminPage() {
  const [{ data }, codexOauthStatusResult] = await Promise.all([
    getAiAgentRegistry(),
    getCodexOauthOperatorStatus().catch(() => null),
  ]);
  const codexOauthStatus =
    codexOauthStatusResult ?? data.runtime_policy.codex_oauth_operator ?? defaultCodexOauthStatus(data.runtime_policy.codex_oauth_status);
  const activeAgentCount = data.agents.length;
  const blockedOrderRatio =
    activeAgentCount > 0 ? Math.round((data.blocked_order_agent_count / activeAgentCount) * 100) : 0;
  const groupedAgents = data.agents.reduce<Record<string, Agent[]>>((groups, agent) => {
    const key = agent.owner_domain || "unknown";
    groups[key] = [...(groups[key] ?? []), agent];
    return groups;
  }, {});

  return (
    <div className="terminal-page">
      <section className="page-hero">
        <div>
          <p className="bento-badge">AI 운영 콘솔</p>
          <h1 className="page-title">에이전트별 모델, fallback, 안전 경계를 한 화면에서 확인한다.</h1>
        </div>
        <p className="page-lede">
          이 화면은 AI가 투자 운영에서 어떤 역할을 맡는지 보여주는 읽기 전용 콘솔이다. 모델 변경, canonical write,
          추천 weight 변경, 주문 제출은 아직 이 화면에서 할 수 없다.
        </p>
      </section>

      <section className="decision-brief" aria-label="AI runtime boundary">
        <div className="decision-brief-main">
          <span className="decision-brief-kicker">현재 실행 경계</span>
          <h2 className="decision-brief-title">배치 AI는 허용, 화면 요청 중 실시간 LLM 호출은 금지.</h2>
          <p className="decision-brief-copy">
            {providerSummary(data)}. {runtimeStatusText(data)}
          </p>
          <div className="decision-brief-meta">
            <span>설정 원천: {data.runtime_policy.configuration_source}</span>
            <span>OpenAI 상태: {data.runtime_policy.primary_provider_status}</span>
            <span>잔액 확인: {data.runtime_policy.openai_provider_health.balance_check_method}</span>
            <span>Codex OAuth: {codexOauthStatus.label}</span>
            <span>주문 경계: {data.runtime_policy.order_boundary}</span>
          </div>
        </div>
        <div className="decision-brief-grid">
          <div className="decision-card is-good">
            <span>등록 에이전트</span>
            <strong>{activeAgentCount}개</strong>
            <small>뉴스, 온톨로지, 사이클, 기업분석, 밸류에이션, 추천 검토, 포트폴리오, 페이퍼 검증을 분리했다.</small>
          </div>
          <div className="decision-card is-good">
            <span>주문 차단</span>
            <strong>{blockedOrderRatio}%</strong>
            <small>모든 에이전트는 실거래·주문 제출 권한이 없다.</small>
          </div>
          <div className="decision-card is-watch">
            <span>OpenAI fallback</span>
            <strong>{data.runtime_policy.primary_provider_status === "known_billing_unavailable" ? "우회 필요" : "상태 확인"}</strong>
            <small>{data.runtime_policy.primary_provider_fallback_reason}</small>
          </div>
          <div className="decision-card is-watch">
            <span>모델 변경</span>
            <strong>{data.runtime_policy.model_editing_enabled ? "활성" : "비활성"}</strong>
            <small>모델 지정 UI는 감사 로그와 승인 경계가 붙기 전까지 열지 않는다.</small>
          </div>
        </div>
      </section>

      <CodexOauthOperatorPanel initialStatus={codexOauthStatus} />

      <section className="decision-brief" aria-label="openai billing status">
        <div className="decision-brief-main">
          <span className="decision-brief-kicker">OpenAI 잔액·쿼터 상태</span>
          <h2 className="decision-brief-title">{data.runtime_policy.openai_provider_health.label}</h2>
          <p className="decision-brief-copy">{data.runtime_policy.openai_provider_health.message}</p>
          <div className="decision-brief-meta">
            <span>상태 코드: {data.runtime_policy.openai_provider_health.status}</span>
            <span>마지막 확인: {formatOptionalDate(data.runtime_policy.openai_provider_health.last_checked_at)}</span>
            <span>다음 재시도: {formatOptionalDate(data.runtime_policy.openai_provider_health.next_retry_at)}</span>
          </div>
        </div>
        <div className="decision-brief-grid">
          <div className="decision-card is-watch">
            <span>남은 잔액</span>
            <strong>
              {data.runtime_policy.openai_provider_health.remaining_balance_usd === null
                ? "공식 API 없음"
                : `$${data.runtime_policy.openai_provider_health.remaining_balance_usd.toFixed(2)}`}
            </strong>
            <small>
              Admin Costs API는 사용 비용을 반환한다. 실제 prepaid 잔액은 Billing Overview에서 확인한다.
            </small>
          </div>
          <div className="decision-card is-good">
            <span>최근 비용</span>
            <strong>{formatUsdAmount(data.runtime_policy.openai_provider_health.cost_status.total_cost_usd)}</strong>
            <small>
              최근 {data.runtime_policy.openai_provider_health.cost_status.lookback_days}일 · 상태{" "}
              {data.runtime_policy.openai_provider_health.cost_status.status}
            </small>
          </div>
          <div className="decision-card is-watch">
            <span>최근 1일 비용</span>
            <strong>{formatUsdAmount(data.runtime_policy.openai_provider_health.cost_status.latest_day_cost_usd)}</strong>
            <small>
              조회 {formatOptionalDate(data.runtime_policy.openai_provider_health.cost_status.last_checked_at)}
            </small>
          </div>
          <div className="decision-card is-good">
            <span>Fallback 1</span>
            <strong>{providerLabel(data.runtime_policy.openai_provider_health.fallback_provider)}</strong>
            <small>OpenAI가 실패하거나 잔액이 없으면 먼저 이 경로로 내려간다.</small>
          </div>
          <div className="decision-card is-good">
            <span>Fallback 2</span>
            <strong>{providerLabel(data.runtime_policy.openai_provider_health.local_fallback_provider)}</strong>
            <small>외부 AI가 모두 실패해도 규칙 기반 분석과 검증은 계속 진행한다.</small>
          </div>
          <div className="decision-card is-watch">
            <span>Admin key</span>
            <strong>{data.runtime_policy.openai_provider_health.admin_api_key_configured ? "설정됨" : "없음"}</strong>
            <small>{data.runtime_policy.openai_provider_health.cost_status.message}</small>
          </div>
        </div>
      </section>

      <section className="flow-panel" aria-label="AI processing flow">
        <div className="section-heading flow-heading">
          <span>AI 처리 순서</span>
          <h2>수집 데이터는 에이전트를 거쳐 후보 근거가 되고, deterministic validator가 최종 반영 여부를 결정한다.</h2>
          <p>
            AI는 번역, 구조화, 연결 설명, 리서치 초안을 만든다. 추천 점수, 포트폴리오 제약, 주문 차단은 코드와 DB
            guardrail이 강제한다.
          </p>
        </div>
        <div className="flow-steps">
          {[
            ["01", "뉴스·지표 수집", "RSS, SEC, FRED, CBOE, Twelve Data가 원천을 모은다."],
            ["02", "에이전트 분석", "번역, 구조화, 온톨로지 매핑, 사이클 해석을 배치로 수행한다."],
            ["03", "자동 검증", "원문 근거 없는 ticker, 낮은 confidence, unknown node를 차단한다."],
            ["04", "근거 저장", "통과한 후보만 canonical event, signal, research artifact로 연결한다."],
            ["05", "추천 검토", "추천은 AI가 직접 결정하지 않고 deterministic component와 thesis가 판단한다."],
            ["06", "주문 차단", "페이퍼 검증까지 읽기 전용이며 실거래 제출은 막혀 있다."],
          ].map(([step, title, copy]) => (
            <div className="flow-step" key={step}>
              <span>{step}</span>
              <strong>{title}</strong>
              <p>{copy}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="decision-page" aria-label="agent cards">
        <div className="section-heading">
          <span>에이전트 목록</span>
          <h2>각 에이전트의 역할과 모델 정책</h2>
          <p>현재는 읽기 전용이다. 모델 교체는 별도 write API, RBAC, audit log가 붙은 뒤에만 허용한다.</p>
        </div>
        {Object.entries(groupedAgents).map(([domain, agents]) => (
          <div className="decision-page" key={domain}>
            <div className="section-heading">
              <span>{domain}</span>
              <h2>{domainLabel(domain)}</h2>
            </div>
            <div className="decision-brief-grid">
              {agents.map((agent) => (
                <AgentCard agent={agent} key={agent.agent_key} />
              ))}
            </div>
          </div>
        ))}
      </section>

      <section className="bento-grid" aria-label="related routes">
        <Link className="route-card" href={"/data-health" as Route}>
          <span>운영 상태</span>
          <strong>수집·AI 실패 확인</strong>
          <small>실패한 배치, OAuth 만료, 알림 목적지, scheduler 상태를 본다.</small>
        </Link>
        <Link className="route-card" href={"/intelligence" as Route}>
          <span>뉴스 AI</span>
          <strong>원천 → AI 근거</strong>
          <small>뉴스 번역, 구조화, validator 결과, 추천 연결을 확인한다.</small>
        </Link>
        <Link className="route-card" href={"/cycle-map" as Route}>
          <span>사이클</span>
          <strong>흐름 지도</strong>
          <small>거시, 도메인, 테마, 종목 사이클의 연결을 본다.</small>
        </Link>
        <Link className="route-card" href={"/trading-readiness" as Route}>
          <span>안전 경계</span>
          <strong>주문 차단 확인</strong>
          <small>페이퍼 검증과 실거래 차단 상태를 분리해서 확인한다.</small>
        </Link>
      </section>
    </div>
  );
}
