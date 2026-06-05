import { getRemediationTickets } from "@/lib/frontend-api";
import { koCode, koLabel, koReason } from "@/lib/korean-labels";

export const dynamic = "force-dynamic";
export const metadata = { title: "보완 큐" };

type RemediationTicket = Awaited<ReturnType<typeof getRemediationTickets>>["data"]["tickets"][number];

type RemediationGroup = {
  key: string;
  symbol: string;
  action: string;
  remediationType: string;
  runner: string;
  requiredDecision: string;
  riskLevel: string;
  latestReason: string;
  latestUpdatedAt: string;
  firstCreatedAt: string;
  ticketCount: number;
  ticketIds: string[];
};

function riskClass(value: string) {
  if (value === "high") {
    return "risk-high";
  }
  if (value === "medium") {
    return "risk-medium";
  }
  return "risk-low";
}

function formatPercent(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return "미설정";
  }
  return `${(value * 100).toFixed(1)}%`;
}

function riskRank(value: string) {
  if (value === "high") {
    return 0;
  }
  if (value === "medium") {
    return 1;
  }
  if (value === "normal") {
    return 2;
  }
  return 3;
}

function formatDateTime(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value || "미확인";
  }
  return new Intl.DateTimeFormat("ko-KR", {
    timeZone: "Asia/Seoul",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function summarizeTicketReason(reason: string) {
  const normalized = koReason(reason).replace(/\s+/g, " ").trim();
  return normalized || "검토 사유가 충분히 연결되지 않았다.";
}

function groupRemediationTickets(tickets: RemediationTicket[]): RemediationGroup[] {
  const groups = new Map<string, RemediationGroup>();
  for (const ticket of tickets) {
    const key = [
      ticket.symbol,
      ticket.action,
      ticket.remediation_type,
      ticket.suggested_runner,
      ticket.required_human_decision,
    ].join("|");
    const current = groups.get(key);
    if (!current) {
      groups.set(key, {
        key,
        symbol: ticket.symbol,
        action: ticket.action,
        remediationType: ticket.remediation_type,
        runner: ticket.suggested_runner,
        requiredDecision: ticket.required_human_decision,
        riskLevel: ticket.risk_level,
        latestReason: ticket.reason,
        latestUpdatedAt: ticket.updated_at,
        firstCreatedAt: ticket.created_at,
        ticketCount: 1,
        ticketIds: [ticket.ticket_id],
      });
      continue;
    }
    current.ticketCount += 1;
    current.ticketIds.push(ticket.ticket_id);
    if (riskRank(ticket.risk_level) < riskRank(current.riskLevel)) {
      current.riskLevel = ticket.risk_level;
    }
    if (new Date(ticket.updated_at).getTime() >= new Date(current.latestUpdatedAt).getTime()) {
      current.latestReason = ticket.reason;
      current.latestUpdatedAt = ticket.updated_at;
    }
    if (new Date(ticket.created_at).getTime() < new Date(current.firstCreatedAt).getTime()) {
      current.firstCreatedAt = ticket.created_at;
    }
  }
  return [...groups.values()].sort((left, right) => {
    const riskDelta = riskRank(left.riskLevel) - riskRank(right.riskLevel);
    if (riskDelta !== 0) {
      return riskDelta;
    }
    if (right.ticketCount !== left.ticketCount) {
      return right.ticketCount - left.ticketCount;
    }
    return new Date(right.latestUpdatedAt).getTime() - new Date(left.latestUpdatedAt).getTime();
  });
}

export default async function RemediationPage() {
  const response = await getRemediationTickets();
  const data = response.data;
  const allocationPolicy = data.allocation_policy;
  const highRiskCount = data.tickets.filter((ticket) => ticket.risk_level === "high").length;
  const groupedTickets = groupRemediationTickets(data.tickets);
  const repeatedGroupCount = groupedTickets.filter((group) => group.ticketCount > 1).length;

  return (
    <div className="terminal-page decision-page">
      <section className="decision-brief reveal" aria-labelledby="remediation-title">
        <div className="decision-brief-main">
          <span className="decision-brief-kicker">보완 큐 · {koLabel(data.portfolio_name)} · {koCode(data.status_filter)}</span>
          <h1 className="decision-brief-title" id="remediation-title">
            먼저 정리해야 할 판단 공백 {data.ticket_count.toLocaleString("ko-KR")}개
          </h1>
          <p className="decision-brief-copy">
            투자 논리 누락, 성과 측정 공백, 비중 검토처럼 자동으로 넘기면 안 되는 항목을 모은다. 실제 상태 변경은 감사 로그와 승인 경로가 준비된 뒤에만 다룬다.
          </p>
          <div className="decision-brief-meta" aria-label="보완 큐 핵심 상태">
            <span>열린 티켓 {data.ticket_count.toLocaleString("ko-KR")}개</span>
            <span>묶은 판단 {groupedTickets.length.toLocaleString("ko-KR")}개</span>
            <span>고위험 {highRiskCount.toLocaleString("ko-KR")}개</span>
            <span>단일 종목 상한 {formatPercent(allocationPolicy.max_single_position_weight)}</span>
            <span>리밸런싱 기준 {formatPercent(allocationPolicy.min_rebalance_target_weight)}</span>
          </div>
        </div>
        <div className="decision-brief-grid">
          <a className={highRiskCount > 0 ? "decision-card is-block" : "decision-card is-good"} href="#remediation-open-items">
            <span>열린 항목</span>
            <strong>{data.ticket_count.toLocaleString("ko-KR")}개</strong>
            <small>고위험 {highRiskCount.toLocaleString("ko-KR")}개. 자동 조치하지 말고 필요한 결정만 확인한다.</small>
            <b>티켓 보기</b>
          </a>
          <a className="decision-card is-watch" href="#remediation-policy">
            <span>비중 정책</span>
            <strong>{formatPercent(allocationPolicy.max_single_position_weight)}</strong>
            <small>추천 비중과 보유 비중 조정은 별도 정책과 승인 경로가 필요하다.</small>
            <b>정책 보기</b>
          </a>
          <a className="decision-card" href="#remediation-status-counts">
            <span>반복 이슈</span>
            <strong>{repeatedGroupCount.toLocaleString("ko-KR")}개</strong>
            <small>같은 판단 공백이 여러 날 반복된 종목을 먼저 본다.</small>
            <b>묶음 보기</b>
          </a>
          <a className="decision-card is-block" href="#remediation-boundary">
            <span>자동 조치</span>
            <strong>금지</strong>
            <small>티켓은 추천이나 주문이 아니라 보완 입력이다.</small>
            <b>경계 보기</b>
          </a>
        </div>
      </section>

      <section className="split-ledger reveal delay-2" id="remediation-open-items">
        <article className="ledger-panel queue-panel">
          <div className="section-heading">
            <span>열린 항목</span>
            <h2>같은 사유는 묶어서 본다</h2>
          </div>
          <p className="decision-copy">
            원장에는 {data.ticket_count.toLocaleString("ko-KR")}개 티켓이 있지만, 화면에서는 같은 종목·같은 조치·같은 판단 사유를 하나로 묶는다.
            반복 횟수가 큰 항목은 같은 문제가 계속 다시 발생한다는 뜻이다.
          </p>
          <div className="remediation-card-grid">
            {groupedTickets.map((group, index) => (
              <article className="remediation-card" key={group.key}>
                <div className="remediation-card-topline">
                  <span>{String(index + 1).padStart(2, "0")}</span>
                  <span className={`risk-tag ${riskClass(group.riskLevel)}`}>{koCode(group.riskLevel)}</span>
                </div>
                <div className="remediation-card-title-row">
                  <h3>{group.symbol}</h3>
                  <strong>{koCode(group.action)}</strong>
                </div>
                <p>{koLabel(group.requiredDecision)}</p>
                <dl className="remediation-card-facts">
                  <div>
                    <dt>반복</dt>
                    <dd>{group.ticketCount.toLocaleString("ko-KR")}건</dd>
                  </div>
                  <div>
                    <dt>구분</dt>
                    <dd>{koCode(group.remediationType)}</dd>
                  </div>
                  <div>
                    <dt>최근 갱신</dt>
                    <dd>{formatDateTime(group.latestUpdatedAt)}</dd>
                  </div>
                  <div>
                    <dt>최초 발생</dt>
                    <dd>{formatDateTime(group.firstCreatedAt)}</dd>
                  </div>
                </dl>
                <div className="remediation-reason">
                  <span>왜 봐야 하나</span>
                  <p>{summarizeTicketReason(group.latestReason)}</p>
                </div>
                <details className="audit-details">
                  <summary>감사용 티켓 식별자 보기</summary>
                  <div className="audit-metadata-grid">
                    <span>처리 경로</span>
                    <strong>{koCode(group.runner)}</strong>
                    <span>티켓 묶음</span>
                    <strong>{group.ticketIds.join(", ")}</strong>
                  </div>
                </details>
              </article>
            ))}
          </div>
        </article>

        <aside className="side-ledger">
          <article className="ledger-panel remediation-side-card" id="remediation-policy">
            <div className="section-heading stacked-heading">
              <span>비중 정책</span>
              <h2>현재 적용 기준</h2>
            </div>
            <p className="decision-copy">
              추천 비중은 신호 크기이고, 보유 비중 축소 여부는 이 정책 기준으로 별도 판단한다.
            </p>
            <div className="remediation-side-grid">
              <article>
                <span>정책</span>
                <strong>{koCode(allocationPolicy.policy_name)}</strong>
              </article>
              <article>
                <span>적용 범위</span>
                <strong>{koCode(allocationPolicy.policy_scope)}</strong>
              </article>
              <article>
                <span>단일 종목 상한</span>
                <strong>{formatPercent(allocationPolicy.max_single_position_weight)}</strong>
              </article>
              <article>
                <span>목표 비중 해석</span>
                <strong>{formatPercent(allocationPolicy.min_rebalance_target_weight)} 이상</strong>
              </article>
            </div>
          </article>

          <article className="ledger-panel remediation-side-card" id="remediation-status-counts">
            <div className="section-heading stacked-heading">
              <span>상태 분포</span>
              <h2>큐 분포</h2>
            </div>
            <div className="remediation-status-list">
              {Object.entries(data.status_counts).map(([status, count]) => (
                <article key={status}>
                  <span>{koCode(status)}</span>
                  <strong>{count.toLocaleString("ko-KR")}개</strong>
                </article>
              ))}
            </div>
          </article>

          <article className="ledger-panel remediation-side-card" id="remediation-boundary">
            <div className="section-heading stacked-heading">
              <span>결정 경계</span>
              <h2>자동 조치 금지</h2>
            </div>
            <p className="decision-copy">
              티켓은 추천이 아니라 운영 입력이다. 실제 보유 판단은 당시 입력 데이터, 점수, thesis,
              무효화 조건을 함께 저장한 뒤 별도 승인 경로에서만 다룬다.
            </p>
            <div className="remediation-boundary-note">
              <strong>이 화면에서 하는 일</strong>
              <p>보완해야 할 판단 공백을 찾는다. 추천 점수, 포트폴리오 비중, 주문 제출은 여기서 바꾸지 않는다.</p>
            </div>
          </article>
        </aside>
      </section>
    </div>
  );
}
