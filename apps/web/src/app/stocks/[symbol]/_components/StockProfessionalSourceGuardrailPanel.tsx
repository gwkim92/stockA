import Link from "next/link";

import type { StockDetailData } from "@/lib/types";

import {
  orderBoundaryLabel,
  professionalGuardrailTitle,
  professionalGuardrailTone,
} from "./stock-professional-audit-model";
import { stockSourceLabel, stockText } from "./stock-detail-panel-format";

type StockProfessionalSourceGuardrailPanelProps = {
  readonly guardrail: StockDetailData["professional_source_guardrail"];
  readonly symbol: string;
};

export function StockProfessionalSourceGuardrailPanel({
  guardrail,
  symbol,
}: StockProfessionalSourceGuardrailPanelProps) {
  const brokerSubmitLabel = guardrail.broker_submit_allowed ? "실거래 가능" : "읽기 전용";
  const brokerSubmitDetail = guardrail.broker_submit_allowed ? "증권사 주문 전송 허용" : "증권사 주문 전송 금지";

  return (
    <section className="bento-card span-4 reveal delay-2" aria-label="투자 판단 사용 가능 여부">
      <div className="section-heading">
        <div>
          <span className="metric-sub">투자 판단 사용 여부</span>
          <h2>{symbol} 분석을 투자 판단 입력으로 써도 되는가</h2>
        </div>
        <span className={`risk-tag ${professionalGuardrailTone(guardrail)}`}>{professionalGuardrailTitle(guardrail)}</span>
      </div>
      <p style={{ color: "var(--text-secondary)", marginTop: 0 }}>
        {stockText(guardrail.summary)} 추천 점수나 보유 비중을 바꾸지 않고, 투자 판단·가상 매매 검증·실거래 가능 여부를
        분리해서 보여준다.
      </p>
      <div className="status-rail compact-rail decision-boundary-rail" aria-label="투자 판단 사용 가능 여부 요약">
        <div className="rail-cell">
          <span>투자 판단 입력</span>
          <strong>{guardrail.professional_decision_use_allowed ? "가능" : "차단"}</strong>
          <small>{stockSourceLabel(guardrail.status)}</small>
        </div>
        <div className="rail-cell">
          <span>가상 매매 검증</span>
          <strong>{guardrail.paper_validation_input_allowed ? "가능" : "차단"}</strong>
          <small>성과 확인 전 입력 여부</small>
        </div>
        <div className="rail-cell">
          <span>부족한 근거</span>
          <strong>{guardrail.blocker_label || "없음"}</strong>
          <small>{guardrail.blocker_code ? stockSourceLabel(guardrail.blocker_code) : "추가 보강 필요 없음"}</small>
        </div>
        <div className="rail-cell rail-critical">
          <span>실거래 상태</span>
          <strong className="rail-status-value">{brokerSubmitLabel}</strong>
          <small>{brokerSubmitDetail} · {orderBoundaryLabel(guardrail.order_boundary)}</small>
        </div>
      </div>
      <div className="empty-state" style={{ marginTop: "18px" }}>
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
