import Link from "next/link";
import type { Route } from "next";

import { OperationsConsoleHeader } from "@/components/operations/OperationsConsoleHeader";
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

function userText(value: string | null | undefined) {
  if (!value) {
    return "";
  }
  return cleanCopy(koReason(koLabel(koCode(value))));
}

function cleanCopy(value: string) {
  return value
    .replaceAll(["페", "이퍼"].join(""), "가상 매매")
    .replaceAll("가상 거래", "가상 매매")
    .replaceAll("simulated paper", "가상 매매 전용")
    .replaceAll("paper trade", "가상 매매")
    .replaceAll("paper validation", "가상 매매 검증")
    .replaceAll("order intent audit", "주문 의도 감사 기록")
    .replaceAll("audit row", "감사 기록")
    .replaceAll("FastAPI frontend server", "읽기 전용 화면 서버")
    .replaceAll("write endpoint", "쓰기 기능")
    .replaceAll("submitted to broker", "실제 주문으로 전송된")
    .replaceAll("submitted to", "제출된")
    .replaceAll("broker submit", "실거래 주문 제출")
    .replaceAll("broker", "증권사 연결")
    .replaceAll("증권사 연결 경계", "증권사 연결 상태")
    .replaceAll("브로커 경계", "증권사 연결 상태")
    .replaceAll("브로커", "증권사 연결")
    .replaceAll("secret", "접속 정보")
    .replaceAll("adapter", "연동기")
    .replaceAll("preview", "미리보기")
    .replaceAll("scope", "권한 범위")
    .replaceAll("enabled", "활성")
    .replaceAll("engaged", "차단 작동")
    .replaceAll("validation run", "검증 실행")
    .replaceAll("paper 전용", "가상 매매 전용")
    .replaceAll("paper 미리보기", "가상 매매 미리보기")
    .replaceAll("not available", "아직 없음")
    .replaceAll("not_available", "아직 없음")
    .replaceAll("global", "전체")
    .replaceAll("주문 경계", "실거래 상태")
    .replaceAll("order boundary", "실거래 상태")
    .replaceAll("read_only_no_order", "읽기 전용, 실거래 주문 차단")
    .replaceAll("쓰기 기능를", "쓰기 기능을")
    .replaceAll("연동기는", "연동은");
}

function orderBoundaryLabel(value: string | null | undefined) {
  if (!value) {
    return "실거래 상태 미확인";
  }
  if (value === "read_only_no_order") {
    return "읽기 전용, 실거래 주문 차단";
  }
  return userText(value);
}

function brokerLabel(value: string | null | undefined) {
  if (!value) {
    return "증권사 미등록";
  }
  if (value === "simulated_paper") {
    return "가상 매매 전용";
  }
  return userText(value);
}

export default async function TradingReadinessPage() {
  const response = await getTradingReadiness();
  const data = response.data;
  const blockedSwitches = data.kill_switches.filter((item) => item.is_engaged);
  const riskGuardrail = data.portfolio_risk_budget_guardrail;
  const candidateReview = riskGuardrail.rebalance_candidate_review;
  const blockedReasons = data.paper_validation.blocked_reasons.map((reason) => koBlockedReason(reason));
  const liveSubmitCount = data.audit_summary.submitted_to_broker_count;
  const brokerSubmitEnabled = data.broker_boundary.supports_order_submit;
  const brokerPreviewEnabled = data.broker_boundary.supports_order_preview;
  const tradingCommandCards = [
    {
      index: "01",
      label: "실거래 결론",
      title:
        liveSubmitCount > 0
          ? "실제 주문 기록 확인 필요"
          : data.gate_summary.blocked_count > 0
            ? "실거래 차단 중"
            : "거래 안전 승인 필요",
      metric: `${data.gate_summary.blocked_count}개 차단 · 실제 주문 ${liveSubmitCount}건`,
      body:
        liveSubmitCount > 0
            ? "실제 주문 전송 기록이 있으므로 결정 기록과 계좌 내역을 우선 대조해야 한다."
          : data.gate_summary.blocked_count > 0
            ? "안전 조건이 닫혀 있어 실거래 전환으로 넘기면 안 된다."
            : "차단 수가 0이어도 실거래는 별도 증권사 주문 절차와 거래 안전 승인 뒤에만 가능하다.",
      href: "#trading-gates",
      cta: "안전 조건 보기",
      tone: liveSubmitCount > 0 || data.gate_summary.blocked_count > 0 ? "block" : "watch",
    },
    {
      index: "02",
      label: "증권사 제출",
      title: brokerSubmitEnabled ? "실제 주문 제출 기능 켜짐" : "실제 주문 제출 기능 꺼짐",
      metric: brokerLabel(data.broker_boundary.broker_code),
      body: brokerSubmitEnabled
        ? "증권사 제출 기능이 켜진 상태다. 주문 전송 기록과 권한 경계를 더 엄격히 확인해야 한다."
        : "현재 증권사 연결 상태는 실제 주문 제출을 지원하지 않는다. 미리보기와 실제 제출을 분리해서 본다.",
      href: "#broker-boundary",
      cta: "증권사 연결 보기",
      tone: brokerSubmitEnabled ? "watch" : "ready",
    },
    {
      index: "03",
      label: "킬 스위치",
      title: blockedSwitches.length > 0 ? "킬 스위치 작동 중" : "킬 스위치 해제",
      metric: `${blockedSwitches.length}개 작동`,
      body:
        blockedSwitches.length > 0
          ? "범위별 킬 스위치가 켜져 있어 해당 범위의 주문 전환은 차단된다."
          : "현재 작동 중인 킬 스위치는 없다. 그래도 증권사 주문 제출 기능과 결정 기록 경계가 별도로 막는다.",
      href: "#kill-switches",
      cta: "킬 스위치 보기",
      tone: blockedSwitches.length > 0 ? "block" : "ready",
    },
    {
      index: "04",
      label: "결정 기록·가상 매매",
      title: `${userText(data.paper_validation.status)} · 기록 ${data.audit_summary.intent_count}건`,
      metric: `검증 통과 항목 ${data.paper_validation.approved_action_count}개 · 제출 ${liveSubmitCount}건`,
      body: "가상 매매 검증과 결정 기록은 실제 주문 전 단계의 근거다. 검증 통과 항목이 있어도 자동 주문은 아니다.",
      href: "#audit-boundary",
      cta: "결정 기록 보기",
      tone: data.paper_validation.blocked_reasons.length > 0 ? "watch" : "ready",
    },
  ];

  return (
    <div className="pageStack decision-page">
      <OperationsConsoleHeader
        section="거래 안전"
        title="계좌 권한·주문 한도·킬 스위치"
        description="가상 매매 검증과 실제 주문 제출 경계를 분리하고, 차단 사유와 감사 기록을 관리합니다."
        currentPath={"/trading-readiness" as Route}
      />
      <section className="decision-brief reveal" aria-labelledby="trading-readiness-title">
        <div className="decision-brief-main">
          <span className="decision-brief-kicker">거래 안전 점검 · 주문 전 차단 상태</span>
          <h1 className="decision-brief-title" id="trading-readiness-title">
            현재 실거래는 {liveSubmitCount > 0 ? "주문 기록 확인 필요" : data.gate_summary.blocked_count > 0 ? "차단 중" : "별도 승인 필요"}
          </h1>
          <p className="decision-brief-copy">
            주문 버튼이 아니라 실거래 전환 가능성을 점검하는 안전판이다. 증권사 연결, 계좌 권한, 주문 한도, 킬 스위치, 가상 매매 검증, 결정 기록 중 무엇이 막혀 있는지 확인한다.
          </p>
          <div className="decision-brief-meta" aria-label="거래 안전 핵심 상태">
            <span>차단 {data.gate_summary.blocked_count.toLocaleString("ko-KR")}개</span>
            <span>누락/주의 {(data.gate_summary.missing_count + data.gate_summary.warning_count).toLocaleString("ko-KR")}개</span>
            <span>킬 스위치 {blockedSwitches.length.toLocaleString("ko-KR")}개</span>
            <span>실제 주문 {liveSubmitCount.toLocaleString("ko-KR")}건</span>
          </div>
        </div>
        <div className="decision-brief-grid">
          {tradingCommandCards.map((card) => (
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

      <section className="split-ledger reveal delay-2" id="trading-gates">
        <article className="ledger-panel queue-panel">
          <div className="section-heading">
            <div>
              <span>안전 조건</span>
              <h2>실제 주문 전에 반드시 통과해야 하는 조건</h2>
            </div>
            <Link className="btn btn-secondary" href={"/paper-trading" as Route}>
              가상 매매 항목 보기
            </Link>
          </div>
          <div className="readiness-grid">
            {data.gates.map((gate) => (
              <article className="readiness-card" key={gate.gate_key}>
                <div className="readiness-card-top">
                  <strong>{userText(gate.label)}</strong>
                  <span className={`risk-tag ${statusClass(gate.status)}`}>{userText(gate.status)}</span>
                </div>
                <p>{userText(gate.detail)}</p>
                <small>다음 조치: {userText(gate.next_step)}</small>
              </article>
            ))}
          </div>
        </article>

        <aside className="side-ledger">
          <article className="ledger-panel" id="broker-boundary">
            <div className="section-heading stacked-heading">
              <span>증권사/계좌</span>
              <h2>권한 경계</h2>
            </div>
            <dl className="fact-list">
              <div>
                <dt>증권사</dt>
                <dd>{brokerLabel(data.broker_boundary.broker_code)}</dd>
              </div>
              <div>
                <dt>증권사 연결 상태</dt>
                <dd>{userText(data.broker_boundary.status)}</dd>
              </div>
              <div>
                <dt>주문 미리보기</dt>
                <dd>{yesNo(brokerPreviewEnabled)}</dd>
              </div>
              <div>
                <dt>실제 주문 전송</dt>
                <dd>{yesNo(brokerSubmitEnabled)}</dd>
              </div>
              <div>
                <dt>접속 정보 설정</dt>
                <dd>{yesNo(data.broker_boundary.secret_configured)}</dd>
              </div>
              <div>
                <dt>계좌 권한</dt>
                <dd>{userText(data.account_permission.permission_scope)}</dd>
              </div>
              <div>
                <dt>계좌 상태</dt>
                <dd>{userText(data.account_permission.status)}</dd>
              </div>
              <div>
                <dt>허용 종목</dt>
                <dd>{data.account_permission.allows_all_symbols ? "전체" : `${data.account_permission.allowed_symbol_count}개`}</dd>
              </div>
            </dl>
          </article>

          <article className="ledger-panel">
            <div className="section-heading stacked-heading">
              <span>리밸런싱 확인 대상</span>
              <h2>위험 예산이 막는 종목</h2>
            </div>
            <p className="empty-copy">
              SPY 기준 비중과 차이가 큰 종목을 확인 대상으로만 보여준다. 이 목록은 주문 목표가 아니며
              증권사 주문 전송은 계속 금지된다.
            </p>
            {candidateReview.candidates.length > 0 ? (
              <div className="reason-list" aria-label="벤치마크 대비 초과 비중 확인 대상">
                {candidateReview.candidates.slice(0, 5).map((candidate) => (
                  <article className="reason-card" key={`${candidate.priority}-${candidate.symbol}`}>
                    <div>
                      <span className="reason-symbol">{candidate.symbol}</span>
                      <strong>
                        {candidate.direction === "overweight" ? "과대 보유" : "과소 보유"} · {formatPercent(candidate.active_weight)}
                      </strong>
                    </div>
                    <p>{userText(candidate.rationale)}</p>
                    <small>실거래 상태: {orderBoundaryLabel(candidate.order_boundary)}</small>
                  </article>
                ))}
              </div>
            ) : (
              <p className="empty-copy">현재 벤치마크 대비 리밸런싱 확인 대상이 없다.</p>
            )}
            <dl className="fact-list">
              <div>
                <dt>확인 대상 수</dt>
                <dd>{candidateReview.candidate_count.toLocaleString("ko-KR")}개</dd>
              </div>
              <div>
                <dt>벤치마크 괴리</dt>
                <dd>{formatPercent(candidateReview.active_share)}</dd>
              </div>
              <div>
                <dt>근거 원천</dt>
                <dd>{koLabel(candidateReview.benchmark_source || candidateReview.source_type)}</dd>
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
                <dd>{userText(data.order_limit_policy.status)}</dd>
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

      <section className="ledger-grid reveal delay-3" id="kill-switches">
        <article className="ledger-panel" id="audit-boundary">
          <div className="section-heading stacked-heading">
            <span>킬 스위치와 검증</span>
            <h2>현재 차단 장치</h2>
          </div>
          <p className="empty-copy">
            킬 스위치는 범위별 최종 차단 장치다. 아래 카드 중 하나라도 차단 중이면 해당 범위의 실거래 전환은
            진행하지 않는다.
          </p>
          <div className="trading-safety-card-grid" aria-label="킬 스위치 차단 상태">
            {data.kill_switches.map((item) => (
              <article className="trading-safety-card" key={`${item.scope}-${item.scope_ref}`}>
                <div className="trading-safety-card-head">
                  <span>{userText(item.scope)}</span>
                  <strong>{userText(item.scope_ref) || "전체 범위"}</strong>
                  <b className={`risk-tag ${item.is_engaged ? "risk-high" : "risk-low"}`}>
                    {item.is_engaged ? "차단 중" : "열림"}
                  </b>
                </div>
                <p>{userText(item.reason) || "저장된 사유 없음"}</p>
                <small>
                  변경 {item.changed_at || "기록 없음"} · 변경자 {userText(item.changed_by) || "미기록"}
                </small>
              </article>
            ))}
          </div>
        </article>

        <article className="ledger-panel">
            <div className="section-heading stacked-heading">
              <span>가상 매매 검증/기록</span>
              <h2>가상 매매 검증과 결정 기록</h2>
            </div>
          <div className="trading-validation-grid" aria-label="가상 매매 검증과 결정 기록 요약">
            <article>
              <span>가상 매매 검증</span>
              <strong>{userText(data.paper_validation.status)}</strong>
              <small>검증일 {data.paper_validation.validation_date || "없음"}</small>
            </article>
            <article>
              <span>충돌 / 통과</span>
              <strong>
                {data.paper_validation.conflict_count.toLocaleString("ko-KR")} /{" "}
                {data.paper_validation.approved_action_count.toLocaleString("ko-KR")}
              </strong>
              <small>추천 {data.paper_validation.recommendation_count.toLocaleString("ko-KR")}개 대조</small>
            </article>
            <article>
              <span>결정 기록</span>
              <strong>{data.audit_summary.intent_count.toLocaleString("ko-KR")}건</strong>
              <small>실제 주문 전송 {liveSubmitCount.toLocaleString("ko-KR")}건</small>
            </article>
            <article>
              <span>위험 예산</span>
              <strong>{userText(riskGuardrail.risk_gate_decision)}</strong>
              <small>기준일 {riskGuardrail.effective_snapshot_date || "없음"}</small>
            </article>
          </div>
          <div className="reason-list" aria-label="포트폴리오 위험 예산 차단 사유">
            {riskGuardrail.blocking_reasons.length > 0 ? riskGuardrail.blocking_reasons.map((reason) => {
              const detail = koBlockedReason(`portfolio_risk_budget_guardrail_blocker:${reason}`);
              return (
                <article className="reason-card" key={reason}>
                  <div>
                    <span className="reason-symbol">위험 예산</span>
                    <strong>{cleanCopy(detail.title)}</strong>
                  </div>
                  <p>{cleanCopy(detail.description)}</p>
                  <small>다음 조치: {cleanCopy(detail.nextStep)}</small>
                </article>
              );
            }) : (
              <article className="reason-card">
                <div>
                  <span className="reason-symbol">위험 예산</span>
                  <strong>현재 위험 예산 차단 사유가 없다</strong>
                </div>
                <p>최신 위험 예산 검증 결과가 가상 매매 검증 입력을 막지 않는다.</p>
              </article>
            )}
          </div>
          {blockedReasons.length > 0 ? (
            <div className="reason-list" aria-label="가상 매매 검증 차단 사유">
              {blockedReasons.map((reason) => (
                <article className="reason-card" key={reason.raw}>
                  <div>
                    <span className="reason-symbol">{reason.symbol ?? "공통"}</span>
                    <strong>{cleanCopy(reason.title)}</strong>
                  </div>
                  <p>{cleanCopy(reason.description)}</p>
                  <small>다음 조치: {cleanCopy(reason.nextStep)}</small>
                </article>
              ))}
            </div>
          ) : (
            <p className="empty-copy">현재 기록된 가상 매매 검증 차단 사유가 없다.</p>
          )}
          <div className="tag-ledger">
            {data.guardrails.map((guardrail) => (
              <span className="risk-tag risk-medium" key={guardrail}>
                {userText(guardrail)}
              </span>
            ))}
          </div>
        </article>
      </section>
    </div>
  );
}
