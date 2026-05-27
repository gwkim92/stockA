import Link from "next/link";
import type { Route } from "next";

import { getTradingReadiness } from "@/lib/frontend-api";
import { koBlockedReason, koCode, koLabel, koReason } from "@/lib/korean-labels";
import type { TradingGateStatus } from "@/lib/types";

export const dynamic = "force-dynamic";
export const metadata = { title: "거래 안전 점검" };

function statusClass(status: TradingGateStatus) {
  if (status === "pass") {
    return "risk-low";
  }
  if (status === "warning") {
    return "risk-medium";
  }
  return "risk-high";
}

function formatCurrency(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return "미설정";
  }
  return new Intl.NumberFormat("ko-KR", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

function formatPercent(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return "미설정";
  }
  return `${Math.round(value * 1000) / 10}%`;
}

function yesNo(value: boolean) {
  return value ? "예" : "아니오";
}

export default async function TradingReadinessPage() {
  const response = await getTradingReadiness();
  const data = response.data;
  const blockedSwitches = data.kill_switches.filter((item) => item.is_engaged);
  const riskGuardrail = data.portfolio_risk_budget_guardrail;
  const candidateReview = riskGuardrail.rebalance_candidate_review;
  const blockedReasons = data.paper_validation.blocked_reasons.map((reason) => koBlockedReason(reason));

  return (
    <div className="pageStack">
      <section className="page-hero reveal" aria-labelledby="trading-readiness-title">
        <div className="bento-badge">거래 안전 점검 • 주문 전 차단 상태</div>
        <h1 id="trading-readiness-title">실제 주문을 넣기 전에 무엇이 막고 있는지 본다.</h1>
        <p>
          증권사 연결, 계좌 권한, 주문 한도, 킬 스위치, 가상 검증, 검토 기록이 모두 통과해야
          실거래 후보가 된다. 아래 거래 안전 요약에서 차단 수와 실제 주문 전송 건수를 먼저 확인한다.
          실제 주문 전송 건수가 0이면 현재 서버에서 실제 주문은 나가지 않았다.
        </p>
      </section>

      <section className="status-rail compact-rail reveal delay-1" aria-label="거래 안전 요약">
        <article className="rail-cell">
          <span>현재 상태</span>
          <strong>{koCode(data.readiness_status)}</strong>
          <small>{koLabel(data.portfolio_name)} · {koCode(data.execution_mode)}</small>
        </article>
        <article className="rail-cell">
          <span>통과</span>
          <strong>{data.gate_summary.pass_count}</strong>
          <small>안전 조건 통과</small>
        </article>
        <article className="rail-cell">
          <span>누락/주의</span>
          <strong>{data.gate_summary.missing_count + data.gate_summary.warning_count}</strong>
          <small>설정 또는 감사 기록 필요</small>
        </article>
        <article className="rail-cell rail-critical">
          <span>차단</span>
          <strong>{data.gate_summary.blocked_count}</strong>
          <small>
            {riskGuardrail.paper_validation_input_allowed
              ? blockedSwitches.length > 0 ? "킬 스위치 포함" : "차단 조건 수"
              : "위험 예산 포함"}
          </small>
        </article>
        <article className="rail-cell">
          <span>실제 주문 전송</span>
          <strong>{data.audit_summary.submitted_to_broker_count}</strong>
          <small>실제 주문 전송 기록</small>
        </article>
      </section>

      <section className="split-ledger reveal delay-2">
        <article className="ledger-panel queue-panel">
          <div className="section-heading">
            <div>
              <span>안전 조건</span>
              <h2>실제 주문 전에 반드시 통과해야 하는 조건</h2>
            </div>
            <Link className="btn btn-secondary" href={"/paper-trading" as Route}>
              가상 거래 후보 보기
            </Link>
          </div>
          <div className="readiness-grid">
            {data.gates.map((gate) => (
              <article className="readiness-card" key={gate.gate_key}>
                <div className="readiness-card-top">
                  <strong>{koLabel(gate.label)}</strong>
                  <span className={`risk-tag ${statusClass(gate.status)}`}>{koCode(gate.status)}</span>
                </div>
                <p>{koLabel(gate.detail)}</p>
                <small>다음 조치: {koReason(gate.next_step)}</small>
              </article>
            ))}
          </div>
        </article>

        <aside className="side-ledger">
          <article className="ledger-panel">
            <div className="section-heading stacked-heading">
              <span>증권사/계좌</span>
              <h2>권한 경계</h2>
            </div>
            <dl className="fact-list">
              <div>
                <dt>증권사</dt>
                <dd>{data.broker_boundary.broker_code || "미등록"}</dd>
              </div>
              <div>
                <dt>증권사 연결 상태</dt>
                <dd>{koCode(data.broker_boundary.status)}</dd>
              </div>
              <div>
                <dt>주문 미리보기</dt>
                <dd>{yesNo(data.broker_boundary.supports_order_preview)}</dd>
              </div>
              <div>
                <dt>실제 주문 전송</dt>
                <dd>{yesNo(data.broker_boundary.supports_order_submit)}</dd>
              </div>
              <div>
                <dt>접속 정보 설정</dt>
                <dd>{yesNo(data.broker_boundary.secret_configured)}</dd>
              </div>
              <div>
                <dt>계좌 권한</dt>
                <dd>{koCode(data.account_permission.permission_scope)}</dd>
              </div>
              <div>
                <dt>계좌 상태</dt>
                <dd>{koCode(data.account_permission.status)}</dd>
              </div>
              <div>
                <dt>허용 종목</dt>
                <dd>{data.account_permission.allows_all_symbols ? "전체" : `${data.account_permission.allowed_symbol_count}개`}</dd>
              </div>
            </dl>
          </article>

          <article className="ledger-panel">
            <div className="section-heading stacked-heading">
              <span>리밸런싱 검토 후보</span>
              <h2>위험 예산이 막는 종목</h2>
            </div>
            <p className="empty-copy">
              SPY 대비 active weight가 큰 종목을 검토 후보로만 보여준다. 이 목록은 주문 목표가 아니며
              증권사 주문 전송은 계속 금지된다.
            </p>
            {candidateReview.candidates.length > 0 ? (
              <div className="reason-list" aria-label="벤치마크 대비 초과 비중 검토 후보">
                {candidateReview.candidates.slice(0, 5).map((candidate) => (
                  <article className="reason-card" key={`${candidate.priority}-${candidate.symbol}`}>
                    <div>
                      <span className="reason-symbol">{candidate.symbol}</span>
                      <strong>
                        {candidate.direction === "overweight" ? "과대 보유" : "과소 보유"} · {formatPercent(candidate.active_weight)}
                      </strong>
                    </div>
                    <p>{candidate.rationale}</p>
                    <small>주문 경계: {koCode(candidate.order_boundary)}</small>
                  </article>
                ))}
              </div>
            ) : (
              <p className="empty-copy">현재 벤치마크 대비 리밸런싱 검토 후보가 없다.</p>
            )}
            <dl className="fact-list">
              <div>
                <dt>후보 수</dt>
                <dd>{candidateReview.candidate_count.toLocaleString("ko-KR")}개</dd>
              </div>
              <div>
                <dt>active share</dt>
                <dd>{formatPercent(candidateReview.active_share)}</dd>
              </div>
              <div>
                <dt>source</dt>
                <dd>{candidateReview.benchmark_source || candidateReview.source_type || "없음"}</dd>
              </div>
            </dl>
          </article>

          <article className="ledger-panel">
            <div className="section-heading stacked-heading">
              <span>주문 한도</span>
              <h2>한도 정책</h2>
            </div>
            <dl className="fact-list">
              <div>
                <dt>정책 상태</dt>
                <dd>{koCode(data.order_limit_policy.status)}</dd>
              </div>
              <div>
                <dt>단일 주문</dt>
                <dd>{formatCurrency(data.order_limit_policy.max_single_order_notional)}</dd>
              </div>
              <div>
                <dt>일일 주문</dt>
                <dd>{formatCurrency(data.order_limit_policy.max_daily_order_notional)}</dd>
              </div>
              <div>
                <dt>비중 변화</dt>
                <dd>{formatPercent(data.order_limit_policy.max_single_order_weight_delta)}</dd>
              </div>
              <div>
                <dt>종목 최대 비중</dt>
                <dd>{formatPercent(data.order_limit_policy.max_post_trade_symbol_weight)}</dd>
              </div>
              <div>
                <dt>현금 버퍼</dt>
                <dd>{formatPercent(data.order_limit_policy.min_cash_buffer_weight)}</dd>
              </div>
            </dl>
          </article>
        </aside>
      </section>

      <section className="ledger-grid reveal delay-3">
        <article className="ledger-panel">
          <div className="section-heading stacked-heading">
            <span>킬 스위치와 검증</span>
            <h2>현재 차단 장치</h2>
          </div>
          <div className="ledger-table-wrap">
            <table className="ledger-table data-health-table">
              <thead>
                <tr>
                  <th scope="col">구분</th>
                  <th scope="col">상태</th>
                  <th scope="col">이유</th>
                  <th scope="col">변경</th>
                </tr>
              </thead>
              <tbody>
                {data.kill_switches.map((item) => (
                  <tr key={`${item.scope}-${item.scope_ref}`}>
                    <td>{koCode(item.scope)} · {item.scope_ref}</td>
                    <td>
                      <span className={`risk-tag ${item.is_engaged ? "risk-high" : "risk-low"}`}>
                        {item.is_engaged ? "차단 중" : "열림"}
                      </span>
                    </td>
                    <td>{koReason(item.reason)}</td>
                    <td>{item.changed_at || "변경 기록 없음"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </article>

        <article className="ledger-panel">
            <div className="section-heading stacked-heading">
              <span>가상 검증/기록</span>
              <h2>가상 검증과 검토 기록</h2>
            </div>
          <dl className="fact-list">
            <div>
              <dt>가상 검증 상태</dt>
              <dd>{koCode(data.paper_validation.status)}</dd>
            </div>
            <div>
              <dt>검증일</dt>
              <dd>{data.paper_validation.validation_date || "없음"}</dd>
            </div>
            <div>
              <dt>충돌 수</dt>
              <dd>{data.paper_validation.conflict_count.toLocaleString("ko-KR")}</dd>
            </div>
            <div>
              <dt>승인 후보</dt>
              <dd>{data.paper_validation.approved_action_count.toLocaleString("ko-KR")}</dd>
            </div>
            <div>
              <dt>검토 기록</dt>
              <dd>{data.audit_summary.intent_count.toLocaleString("ko-KR")}건</dd>
            </div>
            <div>
              <dt>실제 주문 전송</dt>
              <dd>{data.audit_summary.submitted_to_broker_count.toLocaleString("ko-KR")}건</dd>
            </div>
            <div>
              <dt>위험 예산 검증</dt>
              <dd>{koCode(riskGuardrail.risk_gate_decision)}</dd>
            </div>
            <div>
              <dt>위험 예산 기준일</dt>
              <dd>{riskGuardrail.effective_snapshot_date || "없음"}</dd>
            </div>
          </dl>
          <div className="reason-list" aria-label="포트폴리오 위험 예산 차단 사유">
            {riskGuardrail.blocking_reasons.length > 0 ? riskGuardrail.blocking_reasons.map((reason) => {
              const detail = koBlockedReason(`portfolio_risk_budget_guardrail_blocker:${reason}`);
              return (
                <article className="reason-card" key={reason}>
                  <div>
                    <span className="reason-symbol">위험 예산</span>
                    <strong>{detail.title}</strong>
                  </div>
                  <p>{detail.description}</p>
                  <small>다음 조치: {detail.nextStep}</small>
                </article>
              );
            }) : (
              <article className="reason-card">
                <div>
                  <span className="reason-symbol">위험 예산</span>
                  <strong>현재 위험 예산 차단 사유가 없다</strong>
                </div>
                <p>최신 guardrail 결과가 가상 검증 입력을 막지 않는다.</p>
              </article>
            )}
          </div>
          {blockedReasons.length > 0 ? (
            <div className="reason-list" aria-label="가상 검증 차단 사유">
              {blockedReasons.map((reason) => (
                <article className="reason-card" key={reason.raw}>
                  <div>
                    <span className="reason-symbol">{reason.symbol ?? "공통"}</span>
                    <strong>{reason.title}</strong>
                  </div>
                  <p>{reason.description}</p>
                  <small>다음 조치: {reason.nextStep}</small>
                </article>
              ))}
            </div>
          ) : (
            <p className="empty-copy">현재 기록된 가상 검증 차단 사유가 없다.</p>
          )}
          <div className="tag-ledger">
            {data.guardrails.map((guardrail) => (
              <span className="risk-tag risk-medium" key={guardrail}>
                {koLabel(guardrail)}
              </span>
            ))}
          </div>
        </article>
      </section>
    </div>
  );
}
