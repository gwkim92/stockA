import Link from "next/link";

import type { AiEvidenceNeighborhoodData, StockDetailData } from "@/lib/types";

import {
  orderBoundaryLabel,
  stockProfessionalAuditCounts,
  stockProfessionalAuditStatus,
  stockProfessionalLayerStatusLabel,
  stockProfessionalLayerTone,
} from "./stock-professional-audit-model";
import { buildStockProfessionalLayers } from "./stock-professional-layer-model";
import { formatPercent } from "./stock-detail-panel-format";

type StockProfessionalEvidenceAuditPanelProps = {
  readonly data: StockDetailData;
  readonly neighborhood: AiEvidenceNeighborhoodData;
  readonly linkedThesisId: string | null;
  readonly hasPriceData: boolean;
};

export function StockProfessionalEvidenceAuditPanel({
  data,
  neighborhood,
  linkedThesisId,
  hasPriceData,
}: StockProfessionalEvidenceAuditPanelProps) {
  const layers = buildStockProfessionalLayers({ data, neighborhood, linkedThesisId, hasPriceData });
  const counts = stockProfessionalAuditCounts(layers);
  const auditStatus = stockProfessionalAuditStatus(counts);

  return (
    <section className="bento-card span-4 reveal delay-1" aria-label="종목 전문 근거 감사">
      <div className="section-heading">
        <div>
          <span className="metric-sub">전문 근거 감사</span>
          <h2>{data.symbol}을 중장기 판단에 써도 되는가</h2>
        </div>
        <span className={`risk-tag ${auditStatus.tone}`}>{auditStatus.title}</span>
      </div>
      <p style={{ color: "var(--text-secondary)", marginTop: 0, maxWidth: "920px" }}>
        {auditStatus.summary} 이 감사는 저장된 근거가 실제로 남아 있는지 보는 읽기 전용 점검이며 추천 점수, 포지션, 주문을 바꾸지 않는다.
      </p>
      <div className="status-rail compact-rail decision-boundary-rail" aria-label="종목 전문 근거 감사 요약">
        <div className="rail-cell">
          <span>근거 커버리지</span>
          <strong>{formatPercent(counts.coverageRatio)}</strong>
          <small>완료 {counts.completeCount}/{counts.applicableLayers.length} · 일부 {counts.partialCount}</small>
        </div>
        <div className="rail-cell">
          <span>차단·대기</span>
          <strong>{(counts.blockedCount + counts.pendingCount).toLocaleString("ko-KR")}개</strong>
          <small>차단 {counts.blockedCount} · 대기 {counts.pendingCount}</small>
        </div>
        <div className="rail-cell">
          <span>빠진 근거</span>
          <strong>{counts.missingLayers.length.toLocaleString("ko-KR")}개</strong>
          <small>
            {counts.missingLayers.length > 0
              ? counts.missingLayers.slice(0, 2).map((layer) => layer.label).join(", ")
              : "핵심 공백 없음"}
          </small>
        </div>
        <div className="rail-cell rail-critical">
          <span>실거래 상태</span>
          <strong className="rail-status-value">{orderBoundaryLabel(data.professional_source_guardrail.order_boundary)}</strong>
          <small>증권사 주문 {data.professional_source_guardrail.broker_submit_allowed ? "허용" : "차단"}</small>
        </div>
      </div>

      <div className="flow-steps" style={{ marginTop: "18px" }}>
        {counts.applicableLayers.map((layer) => (
          <article className="flow-step" key={layer.key}>
            <span>{layer.label}</span>
            <strong className={`risk-tag ${stockProfessionalLayerTone(layer.status)}`}>
              {stockProfessionalLayerStatusLabel(layer.status)}
            </strong>
            <p>{layer.detail}</p>
            <div className="flow-step-foot">
              <small>원천: {layer.source}</small>
              {layer.href && layer.hrefLabel ? (
                layer.href.startsWith("#") ? (
                  <a href={layer.href}>{layer.hrefLabel} 보기</a>
                ) : (
                  <Link href={layer.href}>{layer.hrefLabel} 보기</Link>
                )
              ) : null}
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
