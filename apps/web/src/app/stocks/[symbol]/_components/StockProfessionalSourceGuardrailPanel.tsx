import Link from "next/link";

import type { StockDetailData } from "@/lib/types";

import {
  orderBoundaryLabel,
  professionalGuardrailTitle,
  professionalGuardrailTone,
} from "./stock-professional-audit-model";
import { stockSourceLabel, stockText } from "./stock-detail-panel-format";
import styles from "./StockProfessionalSourceGuardrailPanel.module.css";

type StockProfessionalSourceGuardrailPanelProps = {
  readonly guardrail: StockDetailData["professional_source_guardrail"];
  readonly symbol: string;
};

function isFundCompanyModelBoundary(guardrail: StockDetailData["professional_source_guardrail"]) {
  return guardrail.blocker_code === "fund_company_financial_model_not_applicable"
    || guardrail.status === "fund_or_etf_company_model_not_applicable";
}

function blockerLabel(guardrail: StockDetailData["professional_source_guardrail"]) {
  if (isFundCompanyModelBoundary(guardrail)) {
    return "회사 재무모델 비대상";
  }
  return guardrail.blocker_label ? stockText(guardrail.blocker_label) : "없음";
}

function blockerDetail(guardrail: StockDetailData["professional_source_guardrail"]) {
  if (isFundCompanyModelBoundary(guardrail)) {
    return "개별 기업 재무제표 대신 보유 구성으로 판단";
  }
  return guardrail.blocker_code ? stockSourceLabel(guardrail.blocker_code) : "추가 보강 필요 없음";
}

function guardrailStatusDetail(guardrail: StockDetailData["professional_source_guardrail"]) {
  if (isFundCompanyModelBoundary(guardrail)) {
    return "펀드형 상품 분석 경계";
  }
  return stockSourceLabel(guardrail.status);
}

export function StockProfessionalSourceGuardrailPanel({
  guardrail,
  symbol,
}: StockProfessionalSourceGuardrailPanelProps) {
  const brokerSubmitLabel = guardrail.broker_submit_allowed ? "실거래 가능" : "읽기 전용";
  const brokerSubmitDetail = guardrail.broker_submit_allowed ? "증권사 주문 전송 허용" : "증권사 주문 전송 금지";

  return (
    <section className="bento-card span-4" aria-label="투자 판단 사용 가능 여부">
      <div className="section-heading">
        <div>
          <span className="metric-sub">투자 판단 사용 여부</span>
          <h2>{symbol} 분석을 투자 판단 입력으로 써도 되는가</h2>
        </div>
        <span className={`risk-tag ${professionalGuardrailTone(guardrail)}`}>{professionalGuardrailTitle(guardrail)}</span>
      </div>
      <p className={styles.copy}>
        {stockText(guardrail.summary)} 추천 점수나 보유 비중을 바꾸지 않고, 투자 판단·가상 매매 검증·실거래 가능 여부를
        분리해서 보여준다.
      </p>
      <div className={`status-rail compact-rail decision-boundary-rail ${styles.rail}`} aria-label="투자 판단 사용 가능 여부 요약">
        <div className="rail-cell">
          <span>투자 판단 입력</span>
          <strong>{guardrail.professional_decision_use_allowed ? "가능" : "차단"}</strong>
          <small>{guardrailStatusDetail(guardrail)}</small>
        </div>
        <div className="rail-cell">
          <span>가상 매매 검증</span>
          <strong>{guardrail.paper_validation_input_allowed ? "가능" : "차단"}</strong>
          <small>성과 확인 전 입력 여부</small>
        </div>
        <div className="rail-cell">
          <span>부족한 근거</span>
          <strong>{blockerLabel(guardrail)}</strong>
          <small>{blockerDetail(guardrail)}</small>
        </div>
        <div className="rail-cell rail-critical">
          <span>실거래 상태</span>
          <strong className="rail-status-value">{brokerSubmitLabel}</strong>
          <small>{brokerSubmitDetail} · {orderBoundaryLabel(guardrail.order_boundary)}</small>
        </div>
      </div>
      <div className={`empty-state ${styles.next}`}>
        <strong>다음 확인</strong>
        <p>{stockText(guardrail.next_action)}</p>
        <div className="btn-row">
          <Link className="btn btn-secondary" href="/data-health">
            원천 상태 보기
          </Link>
          <Link className="btn btn-secondary" href="/paper-trading">
            가상 매매 상태 보기
          </Link>
        </div>
      </div>
    </section>
  );
}
