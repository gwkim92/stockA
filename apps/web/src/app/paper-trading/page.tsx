import Link from "next/link";
import type { Route } from "next";

import { DecisionReviewStrip } from "@/components/decision-review-strip";
import { getPaperTradingPreview, getTradingReadiness } from "@/lib/frontend-api";
import { koBlockedReason, koCode, koLabel, koReason } from "@/lib/korean-labels";
import type { TradingReadinessData } from "@/lib/types";

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
      detail: "실제 주문 전송 기록이 있으므로 검토 기록과 계좌 내역을 먼저 확인해야 한다.",
    };
  }
  if (trading.gate_summary.blocked_count > 0 || trading.paper_validation.blocked_reasons.length > 0) {
    return {
      title: "가상 검증 중 · 실거래 차단",
      tone: "risk-high",
      detail: "가상 후보는 만들 수 있지만 안전 조건이 닫혀 있어 실제 주문으로 넘어가지 않는다.",
    };
  }
  if (trading.paper_validation.approved_action_count > 0) {
    return {
      title: "가상 후보 있음 · 실거래 금지",
      tone: "risk-medium",
      detail: "가상 검증 후보가 있지만 이 화면은 주문을 만들지 않는다. 실거래는 별도 승인, 증권사 연결, 계좌 권한, 주문 한도, 감사 기록이 모두 붙은 뒤에만 가능하다.",
    };
  }
  return {
    title: "가상 후보 대기",
    tone: "risk-medium",
    detail: "추천 후보와 현재 보유 내역이 맞물릴 때 가상 조치 후보가 생성된다.",
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
  const executionSummaryCards = [
    {
      label: "실제 주문",
      title: liveSubmitCount > 0 ? "실제 주문 전송 기록 있음" : "실제 주문 전송 0건",
      body:
        liveSubmitCount > 0
          ? "이 경우 페이퍼 화면을 보기 전에 감사 로그와 실제 계좌 내역을 먼저 대조해야 한다."
          : "현재 서버 기준으로 증권사에 전송된 주문은 없다. 아래 후보는 모두 시뮬레이션이다.",
      tone: liveSubmitCount > 0 ? "risk-high" : "risk-low",
    },
    {
      label: "페이퍼 후보",
      title: simulatedActionCount > 0 ? `${simulatedActionCount}개 시뮬레이션 후보` : "시뮬레이션 후보 없음",
      body:
        simulatedActionCount > 0
          ? "추천과 현재 보유가 충돌하거나 조정 여지가 있는 항목이다. 주문 지시가 아니라 검증용 후보다."
          : "추천, 가격, 보유 데이터가 갱신되면 후보가 다시 계산된다.",
      tone: simulatedActionCount > 0 ? "risk-medium" : "risk-low",
    },
    {
      label: "실거래 전환",
      title: trading.gate_summary.blocked_count > 0 ? "차단됨" : "여전히 별도 승인 필요",
      body:
        trading.gate_summary.blocked_count > 0
          ? "거래 안전 조건이 닫혀 있어 페이퍼 후보를 실거래로 전환하면 안 된다."
          : "차단 조건이 없어 보여도 이 화면에는 주문 버튼이 없다. 실거래 전환은 별도 broker flow에서만 다룬다.",
      tone: trading.gate_summary.blocked_count > 0 ? "risk-high" : "risk-medium",
    },
    {
      label: "다음에 볼 곳",
      title: trading.gate_summary.blocked_count > 0 ? "거래 안전 상태" : simulatedActionCount > 0 ? "후보 상세" : "추천 신호",
      body:
        trading.gate_summary.blocked_count > 0
          ? "차단 사유를 먼저 확인한다. 주문 경계는 계속 읽기 전용이다."
          : simulatedActionCount > 0
            ? "후보별 추천서, 투자 논리, 종목 상세를 열어 근거가 맞는지 확인한다."
            : "추천 후보와 보유 상태가 갱신됐는지 먼저 본다.",
      tone: trading.gate_summary.blocked_count > 0 ? "risk-high" : "risk-medium",
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
      title: "가상 검증 상태",
      value: koCode(trading.paper_validation.status),
      tone: trading.paper_validation.status === "passed" ? "risk-low" : "risk-medium",
      body: `추천 ${trading.paper_validation.recommendation_count}개를 검증했고 승인 후보 ${trading.paper_validation.approved_action_count}개, 충돌 ${trading.paper_validation.conflict_count}개가 있다.`,
    },
    {
      index: "03",
      title: "거래 안전 차단",
      value: `${trading.gate_summary.blocked_count}개`,
      tone: trading.gate_summary.blocked_count > 0 ? "risk-high" : "risk-low",
      body:
        trading.gate_summary.blocked_count > 0
          ? "차단 조건이 남아 있어 실거래 후보로 넘어가지 않는다."
          : "현재 거래 안전 차단 조건은 없지만, 실거래 전 별도 승인이 필요하다.",
    },
    {
      index: "04",
      title: "다음 확인",
      value:
        trading.gate_summary.blocked_count > 0
          ? "거래 안전"
          : data.paper_actions.length > 0
            ? "후보 검토"
            : "추천 대기",
      tone: trading.gate_summary.blocked_count > 0 ? "risk-high" : "risk-medium",
      body:
        trading.gate_summary.blocked_count > 0
          ? "차단 사유를 먼저 풀지 않으면 페이퍼 후보를 실거래로 전환하면 안 된다."
          : data.paper_actions.length > 0
            ? "가상 후보 표에서 종목별 추천, 현재 비중, 목표 비중을 대조한다."
            : "추천이나 보유 내역이 갱신되면 가상 후보가 다시 계산된다.",
    },
    {
      index: "05",
      title: "포트폴리오 위험 예산",
      value: riskGuardrail.paper_validation_input_allowed ? "입력 가능" : "입력 차단",
      tone: riskGuardrail.paper_validation_input_allowed ? "risk-low" : "risk-high",
      body: riskGuardrail.paper_validation_input_allowed
        ? "최신 포트폴리오 위험 예산 검증이 가상 검증 입력을 허용했다."
        : `최신 위험 예산 검증이 ${koCode(riskGuardrail.risk_gate_decision)} 상태라 가상 검증 입력을 막고 있다.`,
    },
  ];
  const decisionSteps = [
    {
      index: "01",
      title: "수집 상태",
      question: "추천 입력이 최신인가",
      status: data.latest_recommendation_batch.as_of_date || "추천 없음",
      body: "페이퍼 검증은 최신 추천과 가격/보유 데이터가 있어야 의미가 있다.",
      href: "/data-health" as Route,
      cta: "수집 상태",
      tone: data.latest_recommendation_batch.as_of_date ? "ok" as const : "watch" as const,
    },
    {
      index: "02",
      title: "뉴스·AI 근거",
      question: "추천 근거가 확인됐나",
      status: `${summary.recommendation_count}개 추천`,
      body: "AI 근거는 추천의 입력일 뿐이고 주문을 직접 결정하지 않는다.",
      href: "/intelligence" as Route,
      cta: "뉴스 AI",
      tone: summary.recommendation_count > 0 ? "ok" as const : "watch" as const,
    },
    {
      index: "03",
      title: "상위 흐름",
      question: "시장 흐름과 충돌하나",
      status: "흐름 확인 필요",
      body: "페이퍼 후보가 상위 흐름과 반대로 움직이는지 사이클맵에서 확인한다.",
      href: "/cycle-map" as Route,
      cta: "흐름 지도",
      tone: "watch" as const,
    },
    {
      index: "04",
      title: "추천·보유",
      question: "보유와 추천이 충돌하나",
      status: `${summary.position_recommendation_conflict_count}개 충돌`,
      body: "추천 액션과 현재 비중이 맞지 않으면 실거래가 아니라 검토 후보로 남긴다.",
      href: "/recommendations" as Route,
      cta: "추천 보기",
      tone: summary.position_recommendation_conflict_count > 0 ? "watch" as const : "ok" as const,
    },
    {
      index: "05",
      title: "페이퍼 안전",
      question: "실거래로 넘어갈 수 있나",
      status: validationState.title,
      body: "이 화면은 가상 주문 검증이다. 증권사 제출은 안전 조건과 별도 승인 전까지 막힌다.",
      href: "/paper-trading" as Route,
      cta: "현재 화면",
      tone: validationState.tone === "risk-high" ? "block" as const : "watch" as const,
    },
  ];

  return (
    <div className="terminal-page">
      <section className="page-hero reveal" aria-labelledby="paper-title">
        <div>
          <div className="bento-badge">가상 거래 • 주문 전 안전 점검</div>
          <h1 className="page-title" id="paper-title">
            현재는 실거래가 아니라 가상 주문 검증 단계다.
          </h1>
        </div>
        <p className="page-lede">
          이 화면은 추천을 바로 주문으로 바꾸지 않는다. 최신 추천과 현재 가상 포트폴리오 보유 내역을 대조해
          “실제로 주문한다면 어떤 조치가 필요할지”만 계산한다. 안전 조건과 검토 기록이 막으면 실거래로 넘어가지 않는다.
        </p>
      </section>

      <DecisionReviewStrip
        activeIndex="05"
        title="페이퍼 거래는 실거래 직전이 아니라 안전 검증 단계다"
        description="추천 후보를 주문으로 바꾸지 않는다. 보유 충돌, 승인 후보, 차단 조건, 실제 주문 제출 여부를 분리해서 본다."
        steps={decisionSteps}
      />

      <section className="feature-map-panel reveal delay-1" aria-labelledby="paper-execution-boundary-title">
        <div className="section-heading stacked-heading">
          <span>현재 결론</span>
          <h2 id="paper-execution-boundary-title">{validationState.title}</h2>
          <p>
            페이퍼 거래 화면은 “실제로 주문했다”가 아니라 “주문한다면 무엇이 문제인지 미리 계산했다”는 뜻이다.
            실제 주문 전송, 시뮬레이션 후보, 차단 조건을 분리해서 본다.
          </p>
        </div>
        <div className="insight-grid">
          {executionSummaryCards.map((card) => (
            <article className="insight-card" key={card.label}>
              <span>{card.label}</span>
              <strong className={`risk-tag ${card.tone}`}>{card.title}</strong>
              <p>{card.body}</p>
            </article>
          ))}
        </div>
        <div className="btn-row decision-actions">
          <Link className="btn btn-primary" href={"/trading-readiness" as Route}>
            거래 안전 상태 보기
          </Link>
          <Link className="btn btn-secondary" href={"/recommendations" as Route}>
            추천 신호 보기
          </Link>
        </div>
      </section>

      <section className="status-rail compact-rail reveal delay-1" aria-label="가상 거래 요약">
        <article className="rail-cell">
          <span>추천 수</span>
          <strong>{summary.recommendation_count}</strong>
          <small>{data.latest_recommendation_batch.as_of_date || "추천 후보 없음"}</small>
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
          <small>안전 조건 확인 필요 {summary.requires_human_approval_count}</small>
        </article>
        <article className="rail-cell">
          <span>실제 주문 제출</span>
          <strong>{trading.audit_summary.submitted_to_broker_count}</strong>
          <small>가상 승인 후보 {trading.paper_validation.approved_action_count}</small>
        </article>
      </section>

      <section className="paper-state-panel reveal delay-1" aria-labelledby="paper-current-state-title">
        <div className="section-heading stacked-heading">
          <span>현재 단계</span>
          <h2 id="paper-current-state-title">{validationState.title}</h2>
          <p>이 상태 카드만 보면 현재가 시뮬레이션 중인지, 차단 중인지, 실제 주문이 나갔는지 바로 알 수 있다.</p>
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
            최신 검증 {riskGuardrail.eval_run_id || "없음"} · 기준일 {riskGuardrail.effective_snapshot_date || "미확인"} ·
            {benchmarkDriftCalculated
              ? ` ${benchmarkCode} 기준 active share ${formatPercent(benchmarkActiveShare)}까지 계산했다.`
              : riskGuardrail.warning_reasons.includes("insufficient_benchmark_composition")
              ? " 벤치마크 구성비가 없어 drift는 아직 계산하지 않는다."
              : " 위험 예산 검증 결과가 페이퍼 검증에 연결되어 있다."}
          </p>
        </div>
        <div className="paper-blocked-reasons" aria-label="벤치마크 리밸런싱 검토 후보">
          <span>리밸런싱 검토 후보</span>
          {candidateReview.candidates.length > 0 ? (
            <div className="relationship-list">
              {candidateReview.candidates.slice(0, 4).map((candidate) => (
                <div className="relationship-chip" key={`${candidate.priority}-${candidate.symbol}`}>
                  <span>{candidate.symbol}</span>
                  <strong>
                    {candidate.direction === "overweight" ? "과대 보유" : "과소 보유"} · {formatPercent(candidate.active_weight)}
                  </strong>
                  <small>{candidate.rationale}</small>
                </div>
              ))}
            </div>
          ) : (
            <p>현재 벤치마크 대비 별도 검토 후보가 없다.</p>
          )}
          <p>
            이 후보는 가상 주문 후보가 아니다. 주문 경계는 {koCode(candidateReview.order_boundary)}이고,
            실제 주문 전송은 계속 금지되어 있다.
          </p>
        </div>
        {blockedReasonDetails.length > 0 ? (
          <div className="paper-blocked-reasons" aria-label="가상 거래 차단 사유">
            <span>차단 사유</span>
            <div className="relationship-list">
              {blockedReasonDetails.slice(0, 6).map((reason) => (
                <div className="relationship-chip" key={reason.raw}>
                  <span>{reason.symbol ? koCode(reason.symbol) : "전체"}</span>
                  <strong>{reason.title}</strong>
                  <small>{reason.description}</small>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="paper-blocked-reasons">
            <span>차단 사유</span>
            <p>현재 가상 검증 차단 사유는 없다. 그래도 실거래 전환은 별도 승인과 증권사 연결 이후에만 가능하다.</p>
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

      <section className="split-ledger reveal delay-2">
        <article className="ledger-panel queue-panel">
          <div className="section-heading">
            <span>시뮬레이션 후보 목록</span>
            <h2>주문이 아니라 검증용 후보만 보여준다</h2>
          </div>
          <div className="ledger-table-wrap">
            <table className="ledger-table data-health-table">
              <thead>
                <tr>
                  <th scope="col">종목</th>
                  <th scope="col">추천</th>
                  <th scope="col">현재 비중</th>
                  <th scope="col">목표 비중</th>
                  <th scope="col">시뮬레이션 조치</th>
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
                      <td>
                        <strong>{koCode(action.paper_action)}</strong>
                        <small>주문 아님</small>
                      </td>
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
                    <td colSpan={7}>현재 시뮬레이션 후보가 없다. 추천 후보나 보유 내역이 갱신되면 다시 표시된다.</td>
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
              아래 후보는 가상 검증 결과다. 실제 주문은 증권사 연결, 계좌 권한, 주문 한도,
              킬 스위치, 검토 기록이 모두 통과해야 별도 단계에서만 다룬다.
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
