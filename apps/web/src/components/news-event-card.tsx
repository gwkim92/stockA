import Link from "next/link";
import type { Route } from "next";

import { koCode } from "@/lib/korean-labels";
import type { EventListData } from "@/lib/types";
import { NewsTitleBlock } from "./news-title-block";

export type NewsEventRow = EventListData["events"][number];

const UNCLASSIFIED_SYMBOL_KEYS = new Set(["", "UNKNOWN", "UNCLASSIFIED"]);

export function isKnownNewsCode(value: string | null | undefined) {
  return Boolean(value && !UNCLASSIFIED_SYMBOL_KEYS.has(value));
}

export function formatNewsPercent(value: number | null | undefined) {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return "미측정";
  }
  return `${Math.round(value * 1000) / 10}%`;
}

export function newsEvidenceHref(evidenceId: string | null | undefined) {
  return evidenceId ? (`/ai-evidence/${encodeURIComponent(evidenceId)}` as Route) : null;
}

export function newsSourceDocumentHref(documentId: string | null | undefined) {
  return documentId ? (`/source-documents/${encodeURIComponent(documentId)}` as Route) : null;
}

export function newsThemeHref(themeKey: string | null | undefined) {
  return themeKey && isKnownNewsCode(themeKey) ? (`/themes/${encodeURIComponent(themeKey)}` as Route) : null;
}

export function newsStockHref(symbol: string | null | undefined) {
  return isKnownNewsCode(symbol) ? (`/stocks/${encodeURIComponent(symbol as string)}` as Route) : null;
}

export function newsCandidateKind(event: NewsEventRow) {
  if (event.ai_evidence_type === "news_event_candidate_rejected" || event.quality_gate === "validator_blocked") {
    return "차단 항목";
  }
  if (event.quality_gate === "low_signal_suppressed") {
    return "저신호 보류";
  }
  if (event.ai_evidence_type === "news_cluster_summary") {
    return "뉴스 묶음";
  }
  return isKnownNewsCode(event.symbol) ? "직접 종목" : "상위 흐름";
}

export function newsQualityLabel(event: NewsEventRow) {
  if (event.quality_gate === "validator_blocked") {
    return "추천 입력 차단";
  }
  if (event.quality_gate === "low_signal_suppressed") {
    return "저신호 보류";
  }
  if (event.ai_evidence_id) {
    return "AI 근거 연결";
  }
  return "AI 구조화 전";
}

type NewsEventCardProps = {
  event: NewsEventRow;
  mode: "ledger" | "classification" | "analysis" | "blocked" | "result";
  compact?: boolean;
};

export function NewsEventCard({ event, mode, compact = false }: NewsEventCardProps) {
  const evidenceLink = newsEvidenceHref(event.ai_evidence_id);
  const documentLink = newsSourceDocumentHref(event.source_document_id);
  const themeLink = newsThemeHref(event.theme_key);
  const stockLink = newsStockHref(event.symbol);
  const classifiedSymbol = isKnownNewsCode(event.symbol);
  const actionLabel = mode === "blocked" ? "차단 이유 보기" : mode === "result" ? "구조화 결과 보기" : "AI 근거 상세";

  return (
    <article className={compact ? "news-row-card news-row-card-compact" : "news-row-card"}>
      <div className="news-row-main">
        <span className="metric-sub">
          {event.event_at} · {koCode(event.event_type)} · {newsCandidateKind(event)}
        </span>
        <NewsTitleBlock
          compact={compact}
          title={event.title}
          koreanTitle={event.korean_title}
          koreanSummary={event.korean_summary}
          translationConfidence={event.translation_confidence}
          symbol={event.symbol}
          themeKey={event.theme_key}
          impactDirection={event.impact_direction}
          impactScore={event.impact_score}
        />
        <div className="tag-strip" aria-label={`${event.title} 해석 태그`}>
          <span>{classifiedSymbol ? `직접 종목 ${koCode(event.symbol)}` : "시장/테마 뉴스"}</span>
          <span>테마 {koCode(event.theme_key)}</span>
          <span>방향 {koCode(event.impact_direction)}</span>
          <span>영향도 {formatNewsPercent(event.impact_score)}</span>
          <span>{newsQualityLabel(event)}</span>
        </div>
      </div>
      <div className="news-row-actions">
        {evidenceLink ? (
          <Link className="btn btn-secondary" href={evidenceLink}>
            {actionLabel}
          </Link>
        ) : null}
        {stockLink ? (
          <Link className="btn btn-secondary" href={stockLink}>
            종목 상세
          </Link>
        ) : null}
        {themeLink ? (
          <Link className="btn btn-secondary" href={themeLink}>
            테마 흐름
          </Link>
        ) : null}
        {documentLink ? (
          <Link className="btn btn-secondary" href={documentLink}>
            원문 열기
          </Link>
        ) : null}
      </div>
    </article>
  );
}
