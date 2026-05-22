import { koCode, koLabel } from "@/lib/korean-labels";

type NewsTitleBlockProps = {
  title: string;
  summary?: string | null;
  symbol?: string | null;
  themeKey?: string | null;
  impactDirection?: string | null;
  impactScore?: number | null;
  compact?: boolean;
};

function isKnownCode(value: string | null | undefined) {
  return Boolean(value && value !== "UNKNOWN" && value !== "UNCLASSIFIED");
}

function isLikelyEnglish(value: string) {
  const latin = (value.match(/[A-Za-z]/g) ?? []).length;
  const hangul = (value.match(/[가-힣]/g) ?? []).length;
  return latin >= 8 && latin > hangul * 2;
}

function formatPercent(value: number | null | undefined) {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return null;
  }
  return `${Math.round(value * 1000) / 10}%`;
}

function interpretationParts(props: NewsTitleBlockProps) {
  const parts: string[] = [];
  if (isKnownCode(props.symbol)) {
    parts.push(`종목 ${koCode(props.symbol as string)}`);
  } else if (isKnownCode(props.themeKey)) {
    parts.push(`상위 흐름 ${koCode(props.themeKey as string)}`);
  }
  if (props.impactDirection) {
    parts.push(`방향 ${koCode(props.impactDirection)}`);
  }
  const impactScore = formatPercent(props.impactScore);
  if (impactScore) {
    parts.push(`영향도 ${impactScore}`);
  }
  return parts;
}

export function NewsTitleBlock(props: NewsTitleBlockProps) {
  const rawTitle = props.title.trim();
  const translatedTitle = koLabel(rawTitle);
  const summary = props.summary?.trim();
  const hasSummary = Boolean(summary && summary !== rawTitle);
  const englishOriginal = isLikelyEnglish(rawTitle);
  const parts = interpretationParts(props);

  return (
    <div className={props.compact ? "news-title-block news-title-block-compact" : "news-title-block"}>
      <span>{hasSummary ? "AI 요약" : englishOriginal ? "원문 제목" : "제목"}</span>
      <strong>{hasSummary ? koLabel(summary as string) : translatedTitle}</strong>
      {hasSummary ? <small>원문 제목: {translatedTitle}</small> : null}
      {parts.length > 0 ? <small>화면 해석: {parts.join(" · ")}</small> : null}
    </div>
  );
}
