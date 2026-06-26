import { getPaperTradingPreview, getTradingReadiness } from "@/lib/frontend-api";
import { koCode } from "@/lib/korean-labels";
import { buildPaperTradingViewModel } from "@/lib/presentation";

import { PaperActionCandidatesSection } from "./_components/PaperActionCandidatesSection";
import { PaperCurrentStatePanel } from "./_components/PaperCurrentStatePanel";
import {
  formatBrokerCash,
  formatPaperPercent,
  paperValidationState,
  recordNumber,
  recordString,
  userFacingText,
} from "./_components/paperTradingFormat";
import styles from "./PaperTradingPage.module.css";

export const dynamic = "force-dynamic";
export const metadata = { title: "가상 매매 점검" };

export default async function PaperTradingPage() {
  const [response, tradingResponse] = await Promise.all([getPaperTradingPreview(), getTradingReadiness()]);
  const data = response.data;
  const trading = tradingResponse.data;
  const paperViewModel = buildPaperTradingViewModel(data);
  const summary = data.quality_summary;
  const validationState = paperValidationState(trading);
  const riskGuardrail = trading.portfolio_risk_budget_guardrail;
  const tossOrderReadiness = trading.tossinvest_order_readiness;
  const primaryBuyingPower = tossOrderReadiness.buying_power[0];
  const brokerBuyingPowerText = primaryBuyingPower
    ? formatBrokerCash(primaryBuyingPower.cash_buying_power, primaryBuyingPower.currency)
    : "현금 정보 없음";
  const benchmarkDrift = riskGuardrail.benchmark_drift;
  const benchmarkDriftCalculated = benchmarkDrift?.drift_calculated === true;
  const benchmarkCode = recordString(benchmarkDrift, "benchmark_code") || "벤치마크";
  const benchmarkActiveShare = recordNumber(benchmarkDrift, "active_share");
  const liveSubmitCount = trading.audit_summary.submitted_to_broker_count;
  const simulatedActionCount = data.paper_actions.length;
  const paperCommandCards = [
    {
      index: "01",
      label: "실제 주문",
      title: liveSubmitCount > 0 ? "실제 주문 전송 기록 있음" : "실제 주문 전송 0건",
      metric: liveSubmitCount > 0 ? `${liveSubmitCount}건 대조 필요` : "증권사 전송 없음",
      body:
        liveSubmitCount > 0
          ? "이 경우 가상 매매 화면보다 감사 로그와 실제 계좌 내역 대조가 우선입니다."
          : "현재 서버 기준으로 증권사에 전송된 주문은 없다. 아래 항목은 모두 검증용 시뮬레이션이다.",
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
          ? "추천과 현재 보유가 충돌하거나 조정 여지가 있는 항목입니다. 실제 실행 전 근거 대조가 필요합니다."
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
          ? "거래 안전 조건이 닫혀 있어 가상 매매 항목은 실거래로 전환되지 않습니다."
          : "차단 조건이 없어 보여도 실거래 전환은 별도 증권사 주문 절차에서만 다룹니다.",
      href: "/trading-readiness",
      cta: "거래 안전 보기",
      tone: trading.gate_summary.blocked_count > 0 ? "block" : "watch",
    },
    {
      index: "04",
      label: "브로커 현실",
      title: tossOrderReadiness.status === "available" || tossOrderReadiness.latest_status === "succeeded"
        ? "토스증권 읽기 완료"
        : "토스증권 데이터 없음",
      metric: `${brokerBuyingPowerText} · 매도 가능 ${tossOrderReadiness.sellable_quantity_count.toLocaleString("ko-KR")}개`,
      body:
        tossOrderReadiness.broker_submit_allowed
          ? "브로커 데이터가 읽혔더라도 실주문 전송은 아직 열지 않는다."
          : "토스 계좌·호가·체결은 실행 현실 확인용이다. 실제 주문 제출은 계속 차단된다.",
      href: "#paper-broker-reality",
      cta: "브로커 현실",
      tone: tossOrderReadiness.status === "available" || tossOrderReadiness.latest_status === "succeeded" ? "ready" : "watch",
    },
    {
      index: "05",
      label: "다음에 볼 곳",
      title: trading.gate_summary.blocked_count > 0 ? "거래 안전 상태" : simulatedActionCount > 0 ? "가상 매매 항목" : "추천 신호",
      metric: trading.gate_summary.blocked_count > 0 ? "차단 사유 우선" : "읽기 전용",
      body:
        trading.gate_summary.blocked_count > 0
          ? "차단 사유가 우선입니다. 실거래 상태는 계속 읽기 전용입니다."
          : simulatedActionCount > 0
            ? "항목별 추천서, 투자 논리, 종목 상세에서 근거 일치 여부를 대조합니다."
            : "추천 신호와 보유 상태의 방향 일치 여부를 표시합니다.",
      href: simulatedActionCount > 0 ? "#paper-action-candidates" : "/recommendations",
      cta: simulatedActionCount > 0 ? "항목 보기" : "추천 보기",
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
          ? "증권사로 전송된 주문 기록이 있습니다. 감사 로그와 계좌 내역 대조가 우선입니다."
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
          ? "차단 조건이 남아 있어 실거래 전환으로 넘어가지 않습니다."
          : "현재 거래 안전 차단 조건은 없지만, 실거래 전 거래 안전 승인이 필요하다.",
    },
    {
      index: "04",
      title: "다음 경로",
      value:
        trading.gate_summary.blocked_count > 0
          ? "거래 안전"
          : data.paper_actions.length > 0
            ? "항목 보기"
            : "추천 대기",
      tone: trading.gate_summary.blocked_count > 0 ? "risk-high" : "risk-medium",
      body:
        trading.gate_summary.blocked_count > 0
          ? "차단 사유가 해소되기 전에는 가상 매매 항목이 실거래로 전환되지 않습니다."
          : data.paper_actions.length > 0
            ? "가상 매매 표에서 종목별 추천, 현재 비중, 목표 비중을 대조합니다."
            : "추천이나 보유 내역이 갱신되면 가상 매매 항목이 다시 계산됩니다.",
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
      <section
        className={`decision-brief workspace-brief paper-command-deck reveal ${styles.paperHeader}`}
        aria-labelledby="paper-title"
      >
        <div className="decision-brief-main">
          <span className="decision-brief-kicker">가상 매매 · 주문 전 안전 점검</span>
          <h1 className="decision-brief-title" id="paper-title">
            {liveSubmitCount > 0
              ? "실제 주문 기록을 즉시 확인해야 합니다."
              : trading.gate_summary.blocked_count > 0
                ? `${paperViewModel.statusLabel} · 가상 후보 ${simulatedActionCount.toLocaleString("ko-KR")}개`
                : `${paperViewModel.statusLabel} · 가상 후보 ${simulatedActionCount.toLocaleString("ko-KR")}개`}
          </h1>
          <p className="decision-brief-copy">
            {paperViewModel.investmentImpact} {paperViewModel.nextAction}
          </p>
          <div className="decision-brief-meta" aria-label="가상 매매 핵심 상태">
            <span>상태 {paperViewModel.statusLabel}</span>
            <span>추천 {summary.recommendation_count.toLocaleString("ko-KR")}개</span>
            <span>가상 항목 {simulatedActionCount.toLocaleString("ko-KR")}개</span>
            <span>차단 {trading.gate_summary.blocked_count.toLocaleString("ko-KR")}개</span>
            <span>적중률 {formatPaperPercent(summary.hit_rate)}</span>
          </div>
        </div>
        <div className="decision-brief-grid workspace-command-grid">
          {paperCommandCards.map((card, index) => (
            <a
              className={`decision-card ${
                index === 0 ? "is-priority" : ""
              } ${
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

      <PaperCurrentStatePanel
        benchmarkActiveShare={benchmarkActiveShare}
        benchmarkCode={benchmarkCode}
        benchmarkDriftCalculated={benchmarkDriftCalculated}
        brokerBuyingPowerText={brokerBuyingPowerText}
        paperStatusCards={paperStatusCards}
        trading={trading}
        validationState={validationState}
      />

      <PaperActionCandidatesSection data={data} />
    </div>
  );
}
