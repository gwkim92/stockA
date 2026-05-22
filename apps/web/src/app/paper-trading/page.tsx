import Link from "next/link";
import type { Route } from "next";

import { getPaperTradingPreview, getTradingReadiness } from "@/lib/frontend-api";
import { koCode, koLabel, koReason } from "@/lib/korean-labels";

export const dynamic = "force-dynamic";
export const metadata = { title: "가상 거래 점검" };

function formatPercent(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return "미측정";
  }
  return `${Math.round(value * 1000) / 10}%`;
}

function formatCurrency(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return "가격 없음";
  }
  return new Intl.NumberFormat("ko-KR", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2,
  }).format(value);
}

function riskClass(value: string) {
  if (value === "high") {
    return "risk-high";
  }
  if (value === "medium") {
    return "risk-medium";
  }
  return "risk-low";
}

function recommendationHref(recommendationId: string | null) {
  return recommendationId ? (`/recommendations/${recommendationId}` as Route) : null;
}

function thesisHref(thesisId: string | null) {
  return thesisId ? (`/theses/${thesisId}` as Route) : null;
}

export default async function PaperTradingPage() {
  const [response, tradingResponse] = await Promise.all([getPaperTradingPreview(), getTradingReadiness()]);
  const data = response.data;
  const trading = tradingResponse.data;
  const summary = data.quality_summary;

  return (
    <div className="terminal-page">
      <section className="page-hero reveal" aria-labelledby="paper-title">
        <div>
          <div className="bento-badge">가상 거래(Paper) • 주문 전 안전 점검</div>
          <h1 className="page-title" id="paper-title">
            실제 주문 전에 추천과 보유 상태가 맞는지 본다.
          </h1>
        </div>
        <p className="page-lede">
          최신 추천과 가상 포트폴리오(Paper) 스냅샷을 대조한다. 이 단계는 주문 전 테스트이며,
          브로커 제출 건수가 0이면 실제 주문은 나가지 않았다.
        </p>
      </section>

      <section className="status-rail compact-rail reveal delay-1" aria-label="가상 거래 품질 요약">
        <article className="rail-cell">
          <span>추천 수</span>
          <strong>{summary.recommendation_count}</strong>
          <small>{data.latest_recommendation_batch.as_of_date || "추천 배치 없음"}</small>
        </article>
        <article className="rail-cell">
          <span>측정 완료</span>
          <strong>{summary.measured_recommendation_count}</strong>
          <small>미측정 {summary.unmeasured_recommendation_count}</small>
        </article>
        <article className="rail-cell">
          <span>적중률</span>
          <strong>{formatPercent(summary.hit_rate)}</strong>
          <small>평균 알파 {formatPercent(summary.average_alpha)}</small>
        </article>
        <article className="rail-cell rail-critical">
          <span>추천/보유 충돌</span>
          <strong>{summary.position_recommendation_conflict_count}</strong>
          <small>사람 승인 필요 {summary.requires_human_approval_count}</small>
        </article>
        <article className="rail-cell">
          <span>브로커 제출</span>
          <strong>{trading.audit_summary.submitted_to_broker_count}</strong>
          <small>가상 승인 후보 {trading.paper_validation.approved_action_count}</small>
        </article>
      </section>

      <section className="feature-map-panel reveal delay-1" aria-labelledby="paper-current-state-title">
        <div className="section-heading stacked-heading">
          <span>현재 단계</span>
          <h2 id="paper-current-state-title">
            {trading.audit_summary.submitted_to_broker_count > 0
              ? "브로커 제출 기록이 있다"
              : "아직 실제 주문은 나가지 않았다"}
          </h2>
        </div>
        <div className="feature-map-grid collection-map-grid">
          <article className="feature-map-card collection-map-card">
            <span>01</span>
            <strong>Paper preview</strong>
            <em>{koCode(trading.execution_mode)}</em>
            <small>추천과 보유 비중을 대조해 가상 조치 후보만 만든다.</small>
          </article>
          <article className="feature-map-card collection-map-card">
            <span>02</span>
            <strong>실제 주문 제출</strong>
            <em>{trading.audit_summary.submitted_to_broker_count}건</em>
            <small>이 숫자가 0이면 브로커로 나간 주문이 없다.</small>
          </article>
          <article className="feature-map-card collection-map-card">
            <span>03</span>
            <strong>안전 관문</strong>
            <em className={`risk-tag ${trading.gate_summary.blocked_count > 0 ? "risk-high" : "risk-low"}`}>
              차단 {trading.gate_summary.blocked_count}개
            </em>
            <small>브로커 경계, 계좌 권한, 주문 한도, 킬 스위치, 감사 로그를 통과해야 다음 단계로 간다.</small>
          </article>
        </div>
      </section>

      <section className="split-ledger reveal delay-2">
        <article className="ledger-panel queue-panel">
          <div className="section-heading">
            <span>가상 거래 테스트 결과</span>
            <h2>추천과 현재 보유가 충돌하는 후보</h2>
          </div>
          <div className="ledger-table-wrap">
            <table className="ledger-table data-health-table">
              <thead>
                <tr>
                  <th scope="col">종목</th>
                  <th scope="col">추천</th>
                  <th scope="col">현재 비중</th>
                  <th scope="col">목표 비중</th>
                  <th scope="col">가상 조치</th>
                  <th scope="col">이유</th>
                  <th scope="col">상세</th>
                </tr>
              </thead>
              <tbody>
                {data.paper_actions.length > 0 ? data.paper_actions.map((action) => {
                  const recommendationLink = recommendationHref(action.recommendation_id);
                  const thesisLink = thesisHref(action.linked_thesis_id);
                  return (
                    <tr key={`${action.symbol}-${action.paper_action}`}>
                      <td>
                        <strong>{action.symbol}</strong>
                        <small>{action.latest_price_date} · {formatCurrency(action.latest_price)}</small>
                      </td>
                      <td>
                        <span className={`risk-tag ${riskClass(action.risk_level)}`}>
                          {koCode(action.recommendation_action)}
                        </span>
                        <small>점수 {formatPercent(action.recommendation_score)}</small>
                      </td>
                      <td>{formatPercent(action.current_weight)}</td>
                      <td>{formatPercent(action.target_weight)}</td>
                      <td>{koCode(action.paper_action)}</td>
                      <td>{koReason(action.reason)}</td>
                      <td>
                        <div className="btn-row" style={{ marginTop: 0 }}>
                          {recommendationLink ? (
                            <Link className="btn btn-secondary" href={recommendationLink}>
                              추천
                            </Link>
                          ) : null}
                          {thesisLink ? (
                            <Link className="btn btn-secondary" href={thesisLink}>
                              논리
                            </Link>
                          ) : null}
                          <Link className="btn btn-secondary" href={`/stocks/${action.symbol}` as Route}>
                            종목
                          </Link>
                        </div>
                      </td>
                    </tr>
                  );
                }) : (
                  <tr>
                    <td colSpan={7}>현재 가상 거래 후보가 없다. 추천 배치나 보유 스냅샷이 갱신되면 다시 표시된다.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </article>

        <aside className="side-ledger">
          <article className="ledger-panel">
            <div className="section-heading stacked-heading">
              <span>안전 경계</span>
              <h2>아직 실제 주문이 아닌 이유</h2>
            </div>
            <p className="empty-copy">
              아래 후보는 가상 검증 결과다. 실제 주문은 브로커 경계, 계좌 권한, 주문 한도,
              킬 스위치, 감사 로그가 모두 통과해야 별도 단계에서만 다룬다.
            </p>
            <div className="tag-ledger">
              {data.guardrails.map((guardrail) => (
                <span className="risk-tag risk-medium" key={guardrail}>
                  {koLabel(guardrail)}
                </span>
              ))}
            </div>
            <div className="btn-row">
              <Link className="btn btn-secondary" href={"/trading-readiness" as Route}>
                거래 안전 상태 보기
              </Link>
            </div>
          </article>

          <article className="ledger-panel">
            <div className="section-heading stacked-heading">
              <span>품질 해석</span>
              <h2>추천 품질 점검</h2>
            </div>
            <dl className="fact-list">
              <div>
                <dt>포트폴리오</dt>
                <dd>{koLabel(data.portfolio_name)}</dd>
              </div>
              <div>
                <dt>전략</dt>
                <dd>{koCode(data.strategy_name)}</dd>
              </div>
              <div>
                <dt>기간</dt>
                <dd>{koCode(data.latest_recommendation_batch.horizon_type)}</dd>
              </div>
              <div>
                <dt>유니버스</dt>
                <dd>{data.latest_recommendation_batch.universe_version}</dd>
              </div>
            </dl>
          </article>
        </aside>
      </section>
    </div>
  );
}
