import Link from "next/link";
import type { Route } from "next";

import { getPaperTradingPreview, getTradingReadiness } from "@/lib/frontend-api";
import { koBlockedReason, koCode, koLabel, koReason } from "@/lib/korean-labels";
import type { TradingReadinessData } from "@/lib/types";

export const dynamic = "force-dynamic";
export const metadata = { title: "가상 매매 점검" };

const USER_FACING_REPLACEMENTS: Array<[string, string]> = [
  ["paper validation", "가상 매매 검증"],
  ["Paper validation", "가상 매매 검증"],
  ["paper trade", "가상 매매"],
  ["가상 거래", "가상 매매"],
  ["broker submit", "증권사 주문 제출"],
  ["broker", "증권사"],
  ["order boundary", "실거래 상태"],
  ["order_boundary", "실거래 상태"],
  ["read_only_no_order", "읽기 전용, 실거래 주문 차단"],
  ["eval_run_id", "검증 기록"],
  ["active share", "벤치마크와 다른 비중"],
  ["drift", "벤치마크 괴리"],
  ["runner", "실행 기록"],
  ["artifact", "결과 기록"],
  ["blocked", "차단"],
  ["pending", "대기"],
  ["approved", "허용"],
  [["페", "이퍼"].join(""), "가상 매매"],
  ["주문 경계", "실거래 상태"],
  ["가중치", "반영 비중"],
];

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

function recordString(record: Record<string, unknown> | undefined, key: string) {
  const value = record?.[key];
  return typeof value === "string" ? value : "";
}

function recordNumber(record: Record<string, unknown> | undefined, key: string) {
  const value = record?.[key];
  if (typeof value === "number") {
    return Number.isFinite(value) ? value : null;
  }
  if (typeof value === "string") {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
}

function userFacingText(value: string | number | boolean | null | undefined) {
  if (value === null || value === undefined || value === "") {
    return "";
  }
  if (typeof value === "number") {
    return value.toLocaleString("ko-KR");
  }
  if (typeof value === "boolean") {
    return value ? "예" : "아니오";
  }
  let text = koLabel(koCode(value));
  for (const [from, to] of USER_FACING_REPLACEMENTS) {
    text = text.replaceAll(from, to);
  }
  return text;
}

function orderBoundaryLabel(value: string | null | undefined) {
  if (!value) {
    return "실거래 상태 미기록";
  }
  if (value === "read_only_no_order") {
    return "읽기 전용, 실거래 주문 차단";
  }
  return userFacingText(value);
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

function paperValidationState(trading: TradingReadinessData) {
  if (trading.audit_summary.submitted_to_broker_count > 0) {
    return {
      title: "실제 주문 전송 기록 있음",
      tone: "risk-high",
      detail: "실제 주문 전송 기록이 있으므로 감사 기록과 계좌 내역을 먼저 대조해야 한다.",
    };
  }
  if (trading.gate_summary.blocked_count > 0 || trading.paper_validation.blocked_reasons.length > 0) {
    return {
      title: "가상 매매 항목 있음 · 실제 주문 차단",
      tone: "risk-high",
      detail: "가상 매매 항목은 만들 수 있지만 안전 조건이 닫혀 있어 실제 주문으로 넘어가지 않는다.",
    };
  }
  if (trading.paper_validation.approved_action_count > 0) {
    return {
      title: "가상 매매 검증 통과 항목 있음 · 실제 주문 금지",
      tone: "risk-medium",
      detail: "가상 매매 검증을 통과한 항목이 있어도 실거래는 닫혀 있다. 거래 안전 승인, 증권사 연결, 계좌 권한, 주문 한도, 감사 기록이 모두 필요하다.",
    };
  }
  return {
    title: "가상 매매 항목 대기 · 실제 주문 없음",
    tone: "risk-medium",
    detail: "추천 신호와 현재 보유 내역이 맞물릴 때 가상 매매 항목이 생성된다.",
  };
}

export default async function PaperTradingPage() {
  const [response, tradingResponse] = await Promise.all([getPaperTradingPreview(), getTradingReadiness()]);
  const data = response.data;
  const trading = tradingResponse.data;
  const summary = data.quality_summary;
  const validationState = paperValidationState(trading);
  const riskGuardrail = trading.portfolio_risk_budget_guardrail;
  const benchmarkDrift = riskGuardrail.benchmark_drift;
  const benchmarkDriftCalculated = benchmarkDrift?.drift_calculated === true;
  const benchmarkCode = recordString(benchmarkDrift, "benchmark_code") || "벤치마크";
  const benchmarkActiveShare = recordNumber(benchmarkDrift, "active_share");
  const candidateReview = riskGuardrail.rebalance_candidate_review;
  const blockedReasonDetails = trading.paper_validation.blocked_reasons.map((reason) => koBlockedReason(reason));
  const liveSubmitCount = trading.audit_summary.submitted_to_broker_count;
  const simulatedActionCount = data.paper_actions.length;
  const paperCommandCards = [
    {
      index: "01",
      label: "실제 주문",
      title: liveSubmitCount > 0 ? "실제 주문 전송 기록 있음" : "실제 주문 전송 0건",
      metric: liveSubmitCount > 0 ? `${liveSubmitCount}건 확인 필요` : "증권사 전송 없음",
      body:
        liveSubmitCount > 0
          ? "이 경우 가상 매매 화면을 보기 전에 감사 로그와 실제 계좌 내역을 먼저 대조해야 한다."
          : "현재 서버 기준으로 증권사에 전송된 주문은 없다. 아래 항목은 모두 검증용이다.",
      href: "#paper-current-state",
      cta: "실거래 상태 보기",
      tone: liveSubmitCount > 0 ? "block" : "ready",
    },
    {
      index: "02",
      label: "가상 매매 검증",
      title: validationState.title,
      metric: simulatedActionCount > 0 ? `${simulatedActionCount}개 항목` : "항목 대기",
      body:
        simulatedActionCount > 0
          ? "추천과 현재 보유가 충돌하거나 조정 여지가 있는 항목이다. 실제 실행 전 근거를 대조한다."
          : "추천, 가격, 보유 데이터가 갱신되면 가상 매매 항목이 다시 계산된다.",
      href: "#paper-action-candidates",
      cta: simulatedActionCount > 0 ? "항목 보기" : "추천 대기 보기",
      tone: simulatedActionCount > 0 ? "watch" : "ready",
    },
    {
      index: "03",
      label: "차단 조건",
      title: trading.gate_summary.blocked_count > 0 ? "실제 주문 차단됨" : "주문 전환은 별도 절차",
      metric: `${trading.gate_summary.blocked_count}개 차단`,
      body:
        trading.gate_summary.blocked_count > 0
          ? "거래 안전 조건이 닫혀 있어 가상 매매 항목을 실거래로 전환하면 안 된다."
          : "차단 조건이 없어 보여도 실거래 전환은 별도 증권사 주문 절차에서만 다룬다.",
      href: "/trading-readiness",
      cta: "거래 안전 보기",
      tone: trading.gate_summary.blocked_count > 0 ? "block" : "watch",
    },
    {
      index: "04",
      label: "다음에 볼 곳",
      title: trading.gate_summary.blocked_count > 0 ? "거래 안전 상태" : simulatedActionCount > 0 ? "가상 매매 항목" : "추천 신호",
      metric: trading.gate_summary.blocked_count > 0 ? "차단 사유 우선" : "읽기 전용 확인",
      body:
        trading.gate_summary.blocked_count > 0
          ? "차단 사유를 먼저 확인한다. 실거래 상태는 계속 읽기 전용이다."
          : simulatedActionCount > 0
            ? "항목별 추천서, 투자 논리, 종목 상세를 열어 근거가 맞는지 확인한다."
            : "추천 신호와 보유 상태가 갱신됐는지 먼저 본다.",
      href: simulatedActionCount > 0 ? "#paper-action-candidates" : "/recommendations",
      cta: simulatedActionCount > 0 ? "항목 확인" : "추천 보기",
      tone: trading.gate_summary.blocked_count > 0 ? "block" : "watch",
    },
  ];
  const paperStatusCards = [
    {
      index: "01",
      title: "실제 주문 제출",
      value: `${liveSubmitCount}건`,
      tone: liveSubmitCount > 0 ? "risk-high" : "risk-low",
      body:
        liveSubmitCount > 0
          ? "증권사로 전송된 주문 기록이 있다. 감사 로그와 계좌 내역을 먼저 대조해야 한다."
          : "현재 이 서버에서 증권사로 전송된 실제 주문은 없다.",
    },
    {
      index: "02",
      title: "가상 매매 항목 검증",
      value: koCode(trading.paper_validation.status),
      tone: trading.paper_validation.status === "passed" ? "risk-low" : "risk-medium",
      body: `추천 ${trading.paper_validation.recommendation_count}개를 대조했고 검증 통과 항목 ${trading.paper_validation.approved_action_count}개, 충돌 ${trading.paper_validation.conflict_count}개가 있다. 통과 항목도 주문 지시는 아니다.`,
    },
    {
      index: "03",
      title: "거래 안전 차단",
      value: `${trading.gate_summary.blocked_count}개`,
      tone: trading.gate_summary.blocked_count > 0 ? "risk-high" : "risk-low",
      body:
        trading.gate_summary.blocked_count > 0
          ? "차단 조건이 남아 있어 실거래 전환으로 넘어가지 않는다."
          : "현재 거래 안전 차단 조건은 없지만, 실거래 전 거래 안전 승인이 필요하다.",
    },
    {
      index: "04",
      title: "다음 확인",
      value:
        trading.gate_summary.blocked_count > 0
          ? "거래 안전"
          : data.paper_actions.length > 0
            ? "항목 확인"
            : "추천 대기",
      tone: trading.gate_summary.blocked_count > 0 ? "risk-high" : "risk-medium",
      body:
        trading.gate_summary.blocked_count > 0
          ? "차단 사유를 먼저 풀지 않으면 가상 매매 항목을 실거래로 전환하면 안 된다."
          : data.paper_actions.length > 0
            ? "가상 매매 표에서 종목별 추천, 현재 비중, 목표 비중을 대조한다."
            : "추천이나 보유 내역이 갱신되면 가상 매매 항목이 다시 계산된다.",
    },
    {
      index: "05",
      title: "포트폴리오 위험 예산",
      value: riskGuardrail.paper_validation_input_allowed ? "입력 가능" : "입력 차단",
      tone: riskGuardrail.paper_validation_input_allowed ? "risk-low" : "risk-high",
      body: riskGuardrail.paper_validation_input_allowed
        ? "최신 포트폴리오 위험 예산 검증이 가상 매매 검증 입력을 허용했다."
        : `최신 위험 예산 검증이 ${userFacingText(riskGuardrail.risk_gate_decision)} 상태라 가상 매매 검증 입력을 막고 있다.`,
    },
  ];
  return (
    <div className="terminal-page decision-page">
      <section className="decision-brief reveal" aria-labelledby="paper-title">
        <div className="decision-brief-main">
          <span className="decision-brief-kicker">가상 매매 · 주문 전 안전 점검</span>
          <h1 className="decision-brief-title" id="paper-title">
            실거래 {liveSubmitCount.toLocaleString("ko-KR")}건, 가상 검증 {simulatedActionCount.toLocaleString("ko-KR")}건.
          </h1>
          <p className="decision-brief-copy">
            추천과 보유 내역을 대조해 실행 가능성을 점검한다. 차단 조건이 남아 있으면 실거래 전환은 닫힌 상태로 유지한다.
          </p>
          <div className="decision-brief-meta" aria-label="가상 매매 핵심 상태">
            <span>추천 {summary.recommendation_count.toLocaleString("ko-KR")}개</span>
            <span>가상 항목 {simulatedActionCount.toLocaleString("ko-KR")}개</span>
            <span>차단 {trading.gate_summary.blocked_count.toLocaleString("ko-KR")}개</span>
            <span>적중률 {formatPercent(summary.hit_rate)}</span>
          </div>
        </div>
        <div className="decision-brief-grid">
          {paperCommandCards.map((card) => (
            <a
              className={`decision-card ${
                card.tone === "ready" ? "is-good" : card.tone === "watch" ? "is-watch" : "is-block"
              }`}
              href={card.href}
              key={card.index}
            >
              <span>{card.label}</span>
              <strong>{card.title}</strong>
              <small>{card.metric} · {card.body}</small>
              <b>{card.cta}</b>
            </a>
          ))}
        </div>
      </section>

      <section className="paper-state-panel reveal delay-1" id="paper-current-state" aria-labelledby="paper-current-state-title">
        <div className="section-heading stacked-heading">
          <span>현재 결론</span>
          <h2 id="paper-current-state-title">{validationState.title}</h2>
          <p>실제 주문 여부, 가상 검증 항목, 차단 조건을 분리해서 본다.</p>
        </div>
        <p className="board-intro">{validationState.detail}</p>
        <div className="paper-state-grid">
          {paperStatusCards.map((card) => (
            <article className="paper-state-card" key={card.index}>
              <span>{card.index}</span>
              <strong>{card.title}</strong>
              <em className={`risk-tag ${card.tone}`}>{card.value}</em>
              <p>{card.body}</p>
            </article>
          ))}
        </div>
        <div className="paper-blocked-reasons" aria-label="포트폴리오 위험 예산 상태">
          <span>위험 예산 연결</span>
          <p>
            위험 예산 검증 {riskGuardrail.eval_run_id ? "기록 있음" : "기록 없음"} · 기준일 {riskGuardrail.effective_snapshot_date || "미확인"} ·
            {benchmarkDriftCalculated
              ? ` ${benchmarkCode} 기준 벤치마크와 다른 비중 ${formatPercent(benchmarkActiveShare)}까지 계산했다.`
              : riskGuardrail.warning_reasons.includes("insufficient_benchmark_composition")
              ? " 벤치마크 구성비가 없어 괴리 계산은 아직 하지 않는다."
              : " 위험 예산 검증 결과가 가상 매매 검증에 연결되어 있다."}
          </p>
        </div>
        <div className="paper-blocked-reasons" aria-label="벤치마크 리밸런싱 확인 대상">
          <span>리밸런싱 확인 대상</span>
          {candidateReview.candidates.length > 0 ? (
            <div className="relationship-list">
              {candidateReview.candidates.slice(0, 4).map((candidate) => (
                <div className="relationship-chip" key={`${candidate.priority}-${candidate.symbol}`}>
                  <span>{candidate.symbol}</span>
                  <strong>
                    {candidate.direction === "overweight" ? "과대 보유" : "과소 보유"} · 벤치마크 대비 {formatPercent(candidate.active_weight)}
                  </strong>
                  <small>{koReason(candidate.rationale)}</small>
                </div>
              ))}
            </div>
          ) : (
            <p>현재 벤치마크 대비 별도 확인 대상이 없다.</p>
          )}
          <p>
            이 항목은 가상 매매 주문 항목이 아니다. 실거래 상태는 {orderBoundaryLabel(candidateReview.order_boundary)}이고,
            실제 주문 전송은 계속 금지되어 있다.
          </p>
        </div>
        {blockedReasonDetails.length > 0 ? (
          <div className="paper-blocked-reasons" aria-label="가상 매매 차단 사유">
            <span>차단 사유</span>
            <div className="relationship-list">
              {blockedReasonDetails.slice(0, 6).map((reason) => (
                <div className="relationship-chip" key={reason.raw}>
                  <span>{reason.symbol ? koCode(reason.symbol) : "전체"}</span>
                  <strong>{userFacingText(reason.title)}</strong>
                  <small>{userFacingText(reason.description)}</small>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="paper-blocked-reasons">
            <span>차단 사유</span>
            <p>현재 가상 매매 검증 차단 사유는 없다. 그래도 실거래 전환은 거래 안전 승인과 증권사 연결 이후에만 가능하다.</p>
          </div>
        )}
        <div className="btn-row decision-actions">
          <Link className="btn btn-primary" href={"/trading-readiness" as Route}>
            거래 안전 상태 보기
          </Link>
          <Link className="btn btn-secondary" href={"/recommendations" as Route}>
            추천 신호 보기
          </Link>
        </div>
      </section>

      <section className="split-ledger reveal delay-2" id="paper-action-candidates">
        <article className="ledger-panel queue-panel">
          <div className="section-heading">
            <span>시뮬레이션 항목 목록</span>
            <h2>주문이 아니라 검증용 항목만 보여준다</h2>
          </div>
          <p className="empty-copy">
            표의 조치는 실제 주문 명령이 아니다. 추천서, 투자 논리, 종목 상세를 대조하기 위한 검증 항목이며,
            이 화면에는 주문 제출 기능이 없다.
          </p>
          {data.paper_actions.length > 0 ? (
            <div className="paper-action-card-grid" aria-label="가상 매매 검증 항목">
              {data.paper_actions.map((action) => {
                const recommendationLink = recommendationHref(action.recommendation_id);
                const thesisLink = thesisHref(action.linked_thesis_id);
                return (
                  <article
                    className={`paper-action-card ${action.conflict ? "is-conflict" : ""}`}
                    key={`${action.symbol}-${action.paper_action}`}
                  >
                    <div className="paper-action-card-head">
                      <span>가상 검증 · 주문 아님</span>
                      <strong>{action.symbol}</strong>
                      <b className={`risk-tag ${riskClass(action.risk_level)}`}>
                        {userFacingText(action.paper_action)}
                      </b>
                    </div>
                    <p>{koReason(action.reason)}</p>
                    <dl className="paper-action-metrics">
                      <div>
                        <dt>현재 비중</dt>
                        <dd>{formatPercent(action.current_weight)}</dd>
                      </div>
                      <div>
                        <dt>목표 비중</dt>
                        <dd>{formatPercent(action.target_weight)}</dd>
                      </div>
                      <div>
                        <dt>추천 점수</dt>
                        <dd>{formatPercent(action.recommendation_score)}</dd>
                      </div>
                    </dl>
                    <div className="paper-action-context">
                      <div>
                        <span>추천 상태</span>
                        <strong>{koCode(action.recommendation_action)}</strong>
                        <small>추천일 {action.recommendation_as_of_date || "미확인"} · 가격일 {action.latest_price_date || "미확인"}</small>
                      </div>
                      <div>
                        <span>실거래 경계</span>
                        <strong>{action.requires_human_approval ? "검증 조건 확인 필요" : "읽기 전용 검증"}</strong>
                        <small>
                          {action.conflict ? "추천과 보유 상태 충돌 있음" : "저장된 충돌 없음"} · 최근 가격 {formatCurrency(action.latest_price)}
                        </small>
                      </div>
                    </div>
                    <div className="paper-action-links">
                      {recommendationLink ? (
                        <Link className="btn btn-secondary" href={recommendationLink}>
                          추천 보기
                        </Link>
                      ) : null}
                      {thesisLink ? (
                        <Link className="btn btn-secondary" href={thesisLink}>
                          투자 논리 보기
                        </Link>
                      ) : null}
                      <Link className="btn btn-secondary" href={`/stocks/${action.symbol}` as Route}>
                        종목 보기
                      </Link>
                    </div>
                  </article>
                );
              })}
            </div>
          ) : (
            <p className="empty-state" style={{ margin: 0 }}>
              현재 시뮬레이션 항목이 없다. 추천 신호나 보유 내역이 갱신되면 다시 표시된다.
            </p>
          )}
        </article>

        <aside className="side-ledger">
          <article className="ledger-panel">
            <div className="section-heading stacked-heading">
              <span>실거래 안전장치</span>
              <h2>아직 실제 주문이 아닌 이유</h2>
            </div>
            <p className="empty-copy">
              아래 항목은 가상 매매 검증 결과다. 실제 주문은 증권사 연결, 계좌 권한, 주문 한도,
              킬 스위치, 감사 기록이 모두 통과해야 별도 단계에서만 다룬다.
            </p>
            <div className="tag-ledger">
              {data.guardrails.map((guardrail) => (
                <span className="risk-tag risk-medium" key={guardrail}>
                  {userFacingText(guardrail)}
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
              <span>성과 해석</span>
              <h2>추천 성과 점검</h2>
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
                <dt>종목군</dt>
                <dd>{data.latest_recommendation_batch.universe_version}</dd>
              </div>
            </dl>
          </article>
        </aside>
      </section>
    </div>
  );
}
