import type { Route } from "next";
import Link from "next/link";

import { koBlockedReason, koCode, koReason } from "@/lib/korean-labels";
import type { TradingReadinessData } from "@/lib/types";

import {
  formatPaperPercent,
  orderBoundaryLabel,
  userFacingText,
} from "./paperTradingFormat";

type PaperStatusCard = {
  readonly body: string;
  readonly index: string;
  readonly title: string;
  readonly tone: string;
  readonly value: string;
};

type PaperCurrentStatePanelProps = {
  readonly benchmarkActiveShare: number | null;
  readonly benchmarkCode: string;
  readonly benchmarkDriftCalculated: boolean;
  readonly brokerBuyingPowerText: string;
  readonly paperStatusCards: readonly PaperStatusCard[];
  readonly trading: TradingReadinessData;
  readonly validationState: {
    readonly detail: string;
    readonly title: string;
  };
};

export function PaperCurrentStatePanel({
  benchmarkActiveShare,
  benchmarkCode,
  benchmarkDriftCalculated,
  brokerBuyingPowerText,
  paperStatusCards,
  trading,
  validationState,
}: PaperCurrentStatePanelProps) {
  const riskGuardrail = trading.portfolio_risk_budget_guardrail;
  const candidateReview = riskGuardrail.rebalance_candidate_review;
  const tossOrderReadiness = trading.tossinvest_order_readiness;
  const blockedReasonDetails = trading.paper_validation.blocked_reasons.map((reason) => koBlockedReason(reason));

  return (
    <section className="paper-state-panel reveal delay-1" id="paper-current-state" aria-labelledby="paper-current-state-title">
      <div className="section-heading stacked-heading">
        <span>현재 결론</span>
        <h2 id="paper-current-state-title">{validationState.title}</h2>
        <p>가상 매매 상태와 실제 주문 차단 사유를 분리해 표시합니다.</p>
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
            ? ` ${benchmarkCode} 기준 벤치마크와 다른 비중 ${formatPaperPercent(benchmarkActiveShare)}까지 계산했습니다.`
            : riskGuardrail.warning_reasons.includes("insufficient_benchmark_composition")
              ? " 벤치마크 구성비가 없어 괴리 계산은 아직 하지 않습니다."
              : " 위험 예산 검증 결과가 가상 매매 검증에 연결되어 있습니다."}
        </p>
      </div>
      <div className="paper-blocked-reasons" aria-label="벤치마크 리밸런싱 후보">
        <span>리밸런싱 후보</span>
        {candidateReview.candidates.length > 0 ? (
          <div className="relationship-list">
            {candidateReview.candidates.slice(0, 4).map((candidate) => (
              <div className="relationship-chip" key={`${candidate.priority}-${candidate.symbol}`}>
                <span>{candidate.symbol}</span>
                <strong>
                  {candidate.direction === "overweight" ? "과대 보유" : "과소 보유"} · 벤치마크 대비{" "}
                  {formatPaperPercent(candidate.active_weight)}
                </strong>
                <small>{koReason(candidate.rationale)}</small>
              </div>
            ))}
          </div>
        ) : (
          <p>현재 벤치마크 대비 별도 후보가 없습니다.</p>
        )}
        <p>
          이 항목은 가상 매매 주문 항목이 아닙니다. 실거래 상태는 {orderBoundaryLabel(candidateReview.order_boundary)}이고,
          실제 주문 전송은 계속 금지되어 있습니다.
        </p>
      </div>
      <div className="paper-blocked-reasons" id="paper-broker-reality" aria-label="토스증권 브로커 현실 데이터">
        <span>토스증권 브로커 현실</span>
        <p>
          토스증권 읽기 전용 결과는 계좌 현금, 매도 가능 수량, 관심 종목 호가·체결, 주의 종목을 확인하는 용도입니다.
          추천 점수와 사이클 계산은 바꾸지 않고, 실제 주문 제출은 {tossOrderReadiness.broker_submit_allowed ? "별도 승인 필요" : "차단"} 상태입니다.
        </p>
        <div className="relationship-list">
          <div className="relationship-chip">
            <span>매수 여력</span>
            <strong>{brokerBuyingPowerText}</strong>
            <small>계좌 기준 통화 {tossOrderReadiness.base_currency || "정보 없음"} · 최근 수집 {tossOrderReadiness.finished_at || "정보 없음"}</small>
          </div>
          <div className="relationship-chip">
            <span>매도 가능</span>
            <strong>{tossOrderReadiness.sellable_quantity_count.toLocaleString("ko-KR")}개 종목</strong>
            <small>보유 수량과 매도 가능 수량을 분리해 실거래 가능성을 표시합니다.</small>
          </div>
          <div className="relationship-chip">
            <span>호가·체결</span>
            <strong>{tossOrderReadiness.market_microdata_symbol_count.toLocaleString("ko-KR")}개 종목</strong>
            <small>브로커 화면의 최신 체결과 호가 근거이며 추천 총점에는 반영하지 않습니다.</small>
          </div>
        </div>
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
          <p>현재 가상 매매 검증 차단 사유는 없습니다. 그래도 실거래 전환은 거래 안전 승인과 증권사 연결 이후에만 가능합니다.</p>
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
  );
}
