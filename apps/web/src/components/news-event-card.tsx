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
    return "투자 근거 연결";
  }
  return "근거 정리 전";
}

function hasStoredKoreanTranslation(event: NewsEventRow) {
  return Boolean(event.korean_title?.trim() || event.korean_summary?.trim());
}

function pathToneClass(tone: "ready" | "watch" | "block") {
  if (tone === "ready") {
    return "is-ready";
  }
  if (tone === "block") {
    return "is-block";
  }
  return "is-watch";
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
  const actionLabel = mode === "blocked" ? "차단 이유 보기" : mode === "result" ? "통과 근거 보기" : "근거 상세";
  const translationReady = hasStoredKoreanTranslation(event);
  const aiBlocked = event.ai_evidence_type === "news_event_candidate_rejected"
    || event.quality_gate === "validator_blocked"
    || mode === "blocked";
  const aiReady = Boolean(event.ai_evidence_id);
  const hasConnection = classifiedSymbol || Boolean(themeLink);
  const pathSteps = [
    {
      label: "원천",
      value: documentLink ? "문서 있음" : "문서 없음",
      tone: documentLink ? "ready" : "watch",
    },
    {
      label: "번역",
      value: translationReady ? "한국어 있음" : "화면 추론",
      tone: translationReady ? "ready" : "watch",
    },
    {
      label: "근거",
      value: aiBlocked ? "차단/보류" : aiReady ? "정리됨" : "대기",
      tone: aiBlocked ? "block" : aiReady ? "ready" : "watch",
    },
    {
      label: "연결",
      value: classifiedSymbol ? `종목 ${koCode(event.symbol)}` : themeLink ? koCode(event.theme_key) : "대기",
      tone: hasConnection ? "ready" : "watch",
    },
  ] as const;

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
        <ol className="news-decision-path" aria-label={`${event.title} 처리 경로`}>
          {pathSteps.map((step) => (
            <li className={pathToneClass(step.tone)} key={step.label}>
              <span>{step.label}</span>
              <strong>{step.value}</strong>
            </li>
          ))}
        </ol>
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
