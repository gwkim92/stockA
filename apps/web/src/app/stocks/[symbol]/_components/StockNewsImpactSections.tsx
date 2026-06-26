import Link from "next/link";
import type { Route } from "next";

import { NewsTitleBlock } from "@/components/news-title-block";
import { koCode, koLabel } from "@/lib/korean-labels";
import type { StockDetailData } from "@/lib/types";

import { formatPercent } from "./stock-detail-panel-format";

type StockNewsImpactSectionsProps = {
  readonly data: StockDetailData;
};

function formatDate(value: string) {
  return value ? value.slice(0, 10) : "날짜 없음";
}

function evidenceHref(evidenceId: string | null) {
  return evidenceId ? (`/ai-evidence/${evidenceId}` as Route) : null;
}

function sourceDocumentHref(documentId: string | null) {
  return documentId ? (`/source-documents/${documentId}` as Route) : null;
}

function cleanFlowText(
  value: string | null | undefined,
  options: {
    readonly themeKey: string;
    readonly symbol: string;
    readonly impactDirection: string;
  },
) {
  const { themeKey, symbol, impactDirection } = options;
  if (!value) {
    return `${koCode(themeKey)} 흐름이 ${koCode(symbol)}에 ${koCode(impactDirection)} 방향으로 전파됐다. 노출도와 신뢰도는 위 수치를 기준으로 본다.`;
  }
  if (/flow propagated to/i.test(value) || /directly exposed/i.test(value)) {
    return `${koCode(themeKey)} 흐름이 ${koCode(symbol)}에 ${koCode(impactDirection)} 방향으로 전파됐다. 자세한 근거는 상세 버튼에서 본다.`;
  }
  const interpretation = value.match(/해석:\s*(.*?)(?:\s*근거:|;\s*노출 근거:|$)/)?.[1]?.trim();
  const evidence = value.match(/근거:\s*(.*?)(?:;\s*노출 근거:|$)/)?.[1]?.trim();
  const exposure = value.match(/노출 근거:\s*(.*)$/)?.[1]?.trim();
  const parts = [
    interpretation ? `해석: ${koLabel(interpretation)}` : null,
    evidence ? `근거: ${koLabel(evidence)}` : null,
    exposure
      ? `노출: ${
          /directly exposed/i.test(exposure)
            ? "이 종목은 해당 테마의 자금 지원·상용화 뉴스에 직접 노출된다."
            : koLabel(exposure)
        }`
      : null,
  ].filter(Boolean);
  if (parts.length > 0) {
    return parts.join(" ");
  }
  return koLabel(value);
}

export function StockNewsImpactSections({ data }: StockNewsImpactSectionsProps) {
  return (
    <>
      <section className="bento-card span-4 reveal delay-4" id="stock-flow-impacts">
        <div className="section-heading">
          <div>
            <span className="metric-sub">상위 흐름 전파</span>
            <h2>회사명이 없어도 거시·테마 흐름은 종목에 영향을 줄 수 있다</h2>
          </div>
          <Link className="btn btn-secondary" href="/intelligence">
            흐름 분석 보기
          </Link>
        </div>
        <p style={{ color: "var(--text-secondary)", marginTop: 0 }}>
          회사가 직접 언급되지 않은 뉴스라도 금리, 에너지, AI 반도체 같은 상위 흐름이면 노출도에 따라 이 종목으로 영향이 전파된다.
        </p>
        <div className="bento-list">
          {data.macro_flow_impacts.length > 0 ? (
            data.macro_flow_impacts.map((flow) => {
              const evidence = evidenceHref(flow.ai_evidence_id);
              const sourceDocument = sourceDocumentHref(flow.source_document_id);
              const flowRationale = cleanFlowText(flow.rationale, {
                themeKey: flow.theme_key,
                symbol: data.symbol,
                impactDirection: flow.impact_direction,
              });
              return (
                <div className="bento-list-item" key={`${flow.event_id}-${flow.theme_key}`}>
                  <div>
                    <span className="metric-sub">
                      {formatDate(flow.event_at)} • {koCode(flow.theme_key)} • {koCode(flow.impact_direction)}
                    </span>
                    <NewsTitleBlock
                      title={flow.title}
                      koreanTitle={flow.korean_title}
                      koreanSummary={flow.korean_summary}
                      translationConfidence={flow.translation_confidence}
                      symbol={data.symbol}
                      themeKey={flow.theme_key}
                      impactDirection={flow.impact_direction}
                      impactScore={flow.impact_score}
                    />
                    <span>
                      전파 강도 {formatPercent(flow.impact_score)} · 노출도 {formatPercent(flow.exposure_weight)} · 신뢰도 {formatPercent(flow.confidence)}
                    </span>
                    {flowRationale ? <span className="flow-rationale">{flowRationale}</span> : null}
                  </div>
                  <div className="btn-row" style={{ marginTop: 0 }}>
                    <Link className="btn btn-secondary" href={`/themes/${encodeURIComponent(flow.theme_key)}?asOfDate=${encodeURIComponent(data.as_of_date)}` as Route}>
                      흐름 보기
                    </Link>
                    {evidence ? <Link className="btn btn-secondary" href={evidence}>근거 상세</Link> : null}
                    {sourceDocument ? <Link className="btn btn-secondary" href={sourceDocument}>근거 문서</Link> : null}
                  </div>
                </div>
              );
            })
          ) : (
            <div className="empty-state">
              아직 이 종목으로 전파된 상위 흐름이 없다. 직접 뉴스만 있거나 종목 민감도 연결이 부족한 상태다.
            </div>
          )}
        </div>
      </section>

      <section className="bento-card span-4 reveal delay-4" id="stock-direct-events">
        <div className="section-heading">
          <div>
            <span className="metric-sub">직접 뉴스</span>
            <h2>회사나 티커가 직접 연결된 뉴스만 따로 본다</h2>
          </div>
          <Link className="btn btn-secondary" href={`/events?symbol=${encodeURIComponent(data.symbol)}` as Route}>
            수집 뉴스
          </Link>
        </div>
        <div className="bento-list">
          {data.recent_events.length > 0 ? (
            data.recent_events.map((event) => {
              const evidence = evidenceHref(event.ai_evidence_id);
              const sourceDocument = sourceDocumentHref(event.source_document_id);
              return (
                <div className="bento-list-item" key={event.event_id}>
                  <div>
                    <span className="metric-sub">{formatDate(event.event_at)} • {koCode(event.event_type)}</span>
                    <NewsTitleBlock
                      title={event.title}
                      koreanTitle={event.korean_title}
                      koreanSummary={event.korean_summary}
                      translationConfidence={event.translation_confidence}
                      symbol={data.symbol}
                      impactDirection={event.impact_direction}
                      impactScore={event.impact_score}
                    />
                    <span>{koCode(event.impact_direction)} • 영향도 {formatPercent(event.impact_score)}</span>
                  </div>
                  <div className="btn-row" style={{ marginTop: 0 }}>
                    {evidence ? <Link className="btn btn-secondary" href={evidence}>근거 상세</Link> : null}
                    {sourceDocument ? <Link className="btn btn-secondary" href={sourceDocument}>근거 문서</Link> : null}
                  </div>
                </div>
              );
            })
          ) : (
            <div className="empty-state">아직 이 종목에 연결된 이벤트가 없다.</div>
          )}
        </div>
      </section>
    </>
  );
}

