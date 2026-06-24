import { koCode, koLabel } from "@/lib/korean-labels";

type NewsTitleBlockProps = {
  title: string;
  summary?: string | null;
  koreanTitle?: string | null;
  koreanSummary?: string | null;
  translationConfidence?: number | null;
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

function hasHangul(value: string) {
  return /[가-힣]/.test(value);
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
    parts.push(`영향 ${impactScore}`);
  }
  return parts;
}

function koreanDigest(props: NewsTitleBlockProps, rawTitle: string, summary: string | null | undefined) {
  const storedTitle = props.koreanTitle?.trim();
  const storedSummary = props.koreanSummary?.trim();
  if (storedTitle) {
    return storedSummary && storedSummary !== storedTitle ? `${storedTitle} · ${storedSummary}` : storedTitle;
  }

  const candidate = summary?.trim() || rawTitle;
  const translated = koLabel(candidate);
  if (hasHangul(candidate) && !isLikelyEnglish(candidate)) {
    return translated;
  }
  if (hasHangul(translated) && translated !== rawTitle) {
    return translated;
  }

  const target = isKnownCode(props.symbol)
    ? `${koCode(props.symbol as string)} 관련 뉴스`
    : isKnownCode(props.themeKey)
      ? `${koCode(props.themeKey as string)} 흐름 뉴스`
      : "시장 뉴스";
  const direction = props.impactDirection ? `${koCode(props.impactDirection)} 신호` : "방향 미분류";
  const impactScore = formatPercent(props.impactScore);
  return impactScore ? `${target} · ${direction} · 영향 ${impactScore}` : `${target} · ${direction}`;
}

export function NewsTitleBlock(props: NewsTitleBlockProps) {
  const rawTitle = props.title.trim();
  const summary = props.summary?.trim();
  const hasSummary = Boolean(summary && summary !== rawTitle);
  const englishOriginal = isLikelyEnglish(rawTitle);
  const digest = koreanDigest(props, rawTitle, summary);
  const parts = interpretationParts(props);
  const confidence = formatPercent(props.translationConfidence);
  const hasStoredTranslation = Boolean(props.koreanTitle?.trim() || props.koreanSummary?.trim());

  return (
    <div className={props.compact ? "news-title-block news-title-block-compact" : "news-title-block"}>
      <span>{hasStoredTranslation ? "한국어 요약" : englishOriginal || hasSummary ? "AI 요약" : "뉴스 제목"}</span>
      <strong>{digest}</strong>
      {hasStoredTranslation && confidence ? <small>번역 신뢰도 {confidence}</small> : null}
      {parts.length > 0 ? <small>투자 해석: {parts.join(" · ")}</small> : null}
      {englishOriginal ? (
        <details className="news-original-title">
          <summary>영어 원문 제목 보기</summary>
          <small>{rawTitle}</small>
        </details>
      ) : null}
    </div>
  );
}
