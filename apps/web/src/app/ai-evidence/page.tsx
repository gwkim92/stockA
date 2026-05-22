import Link from "next/link";
import type { Route } from "next";

import { NewsTitleBlock } from "@/components/news-title-block";
import { getEvents } from "@/lib/frontend-api";
import { koCode, koLabel } from "@/lib/korean-labels";
import type { EventListData } from "@/lib/types";

export const dynamic = "force-dynamic";
export const metadata = { title: "뉴스 AI 후보" };

function formatPercent(value: number | null) {
  if (value === null) {
    return "신뢰도 미제공";
  }
  return `신뢰도 ${Math.round(value * 1000) / 10}%`;
}

function evidenceHref(evidenceId: string) {
  return `/ai-evidence/${encodeURIComponent(evidenceId)}` as Route;
}

function sourceDocumentHref(documentId: string | null) {
  return documentId ? (`/source-documents/${encodeURIComponent(documentId)}` as Route) : null;
}

type NewsCandidateEvent = EventListData["events"][number];

const UNCLASSIFIED_SYMBOL_KEYS = new Set(["", "UNKNOWN", "UNCLASSIFIED"]);

function hasClassifiedSymbol(event: NewsCandidateEvent) {
  return Boolean(event.symbol && !UNCLASSIFIED_SYMBOL_KEYS.has(event.symbol));
}

function candidateKindLabel(event: NewsCandidateEvent) {
  return hasClassifiedSymbol(event) ? "직접 종목 후보" : "상위 흐름 후보";
}

function candidateDetailButtonLabel(event: NewsCandidateEvent) {
  return hasClassifiedSymbol(event) ? "종목 근거 상세" : "흐름 근거 상세";
}

function candidatePrimaryChip(event: NewsCandidateEvent) {
  return hasClassifiedSymbol(event)
    ? {
        label: "직접 종목",
        value: koCode(event.symbol),
        description: "종목 뉴스는 보유검토와 추천 점수의 직접 근거가 될 수 있다.",
      }
    : {
        label: "상위 흐름",
        value: koCode(event.theme_key),
        description: "거시·테마 뉴스는 관련 종목군으로 전파되는 상위 입력이다.",
      };
}

function candidatePurpose(event: NewsCandidateEvent) {
  if (hasClassifiedSymbol(event)) {
    return "AI가 뉴스 한 건을 특정 종목, 테마, 방향, 불확실성으로 구조화했다.";
  }
  return "AI가 종목을 억지로 붙이지 않고 거시·테마 흐름으로 구조화했다. 이후 노출도 규칙으로 관련 종목에 전파된다.";
}

function CandidateCard({ event }: { event: NewsCandidateEvent }) {
  const primaryChip = candidatePrimaryChip(event);
  const evidenceLink = evidenceHref(event.ai_evidence_id as string);
  const documentLink = sourceDocumentHref(event.source_document_id);

  return (
    <article className="trace-card" key={`${event.event_id}-${event.ai_evidence_id}`}>
      <div className="trace-card-top">
        <div>
          <span className="metric-sub">
            {koCode(event.symbol)} • {koCode(event.event_type)} • {event.event_at}
          </span>
          <NewsTitleBlock
            title={event.title}
            symbol={event.symbol}
            themeKey={event.theme_key}
            impactDirection={event.impact_direction}
            impactScore={event.impact_score}
          />
        </div>
        <span className="relation-pill">{candidateKindLabel(event)}</span>
      </div>

      <div className="evidence-strip">
        <span>분석 상태</span>
        <strong>{koCode(event.ai_evidence_provider)} · {formatPercent(event.ai_evidence_confidence)}</strong>
        <p>{candidatePurpose(event)}</p>
      </div>

      <div className="relationship-panel" aria-label={`${event.title} AI 후보 연결`}>
        <span>추천 판단에 들어가기 전 확인할 근거 경로</span>
        <div className="relationship-list">
          <div className="relationship-chip">
            <span>{primaryChip.label}</span>
            <strong>{primaryChip.value}</strong>
            <small>{primaryChip.description}</small>
          </div>
          <div className="relationship-chip">
            <span>방향</span>
            <strong>{koCode(event.impact_direction)}</strong>
            <small>영향도 {Math.round(event.impact_score * 1000) / 10}% · {koCode(event.quality_gate)}</small>
          </div>
          <div className="relationship-chip">
            <span>다음 화면</span>
            <strong>상세 근거</strong>
            <small>AI 추출 필드, 원천 문서, 검증 상태를 확인한다.</small>
          </div>
        </div>
      </div>

      <div className="btn-row">
        <Link className="btn btn-primary" href={evidenceLink}>
          {candidateDetailButtonLabel(event)}
        </Link>
        <Link className="btn btn-secondary" href="/events">
          이벤트 원장
        </Link>
        {documentLink ? (
          <Link className="btn btn-secondary" href={documentLink}>
            원천 문서
          </Link>
        ) : null}
      </div>
    </article>
  );
}

export default async function AiEvidenceIndexPage() {
  const [response, allEventsResponse] = await Promise.all([
    getEvents({ evidenceType: "news_event_candidate", limit: 50 }),
    getEvents({ limit: 1 }),
  ]);
  const data = response.data;
  const allSummary = allEventsResponse.data.summary;
  const candidates = data.events.filter((event) => event.ai_evidence_id);
  const newsCandidates = candidates.filter((event) => event.ai_evidence_type === "news_event_candidate");
  const directNewsCandidates = newsCandidates.filter(hasClassifiedSymbol);
  const macroNewsCandidates = newsCandidates.filter((event) => !hasClassifiedSymbol(event));
  const clusterEvidenceCount = allSummary.news_cluster_summary_count;
  const suppressedLowSignalCount = data.summary.suppressed_low_signal_candidate_count;

  return (
    <div className="pageStack">
      <section className="page-hero reveal" aria-labelledby="ai-evidence-index-title">
        <div>
          <div className="bento-badge">뉴스 AI 근거 • {data.as_of_date}</div>
          <h1 className="page-title" id="ai-evidence-index-title">
            AI가 해석한 뉴스 후보를 한 곳에서 본다.
          </h1>
        </div>
        <p className="page-lede">
          이 화면은 한 뉴스 단위로 AI가 구조화한 후보만 모은다. 종목이 없는 저신호 일반 top story는
          기본 후보에서 숨기고, 여러 뉴스를 묶은 흐름 증거는 뉴스·AI 판단 화면에서 따로 확인한다.
        </p>
      </section>

      <section className="status-rail compact-rail reveal delay-1" aria-label="뉴스 AI 후보 요약">
        <div className="rail-cell">
          <span>AI 연결 이벤트</span>
          <strong>{allSummary.ai_extracted_count}</strong>
          <small>후보와 묶음 근거 전체</small>
        </div>
        <div className="rail-cell">
          <span>직접 종목 후보</span>
          <strong>{directNewsCandidates.length}</strong>
          <small>종목 보유검토에 직접 연결</small>
        </div>
        <div className="rail-cell">
          <span>상위 흐름 후보</span>
          <strong>{macroNewsCandidates.length}</strong>
          <small>거시·테마 흐름으로 전파</small>
        </div>
        <div className="rail-cell">
          <span>뉴스 묶음 근거</span>
          <strong>{clusterEvidenceCount}</strong>
          <small>목록에서는 제외, 뉴스·AI에서 확인</small>
        </div>
        <div className="rail-cell">
          <span>품질 필터 숨김</span>
          <strong>{suppressedLowSignalCount}</strong>
          <small>종목 없는 저신호 후보는 원장에만 보존</small>
        </div>
      </section>

      <section className="bento-card span-4 reveal delay-2" aria-labelledby="ai-evidence-candidate-list-title">
        <div className="section-heading stacked-heading">
          <span>최신 후보</span>
          <h2 id="ai-evidence-candidate-list-title">직접 종목 뉴스 후보</h2>
        </div>
        <p className="relationship-empty">
          여기에 보이는 후보는 특정 종목에 직접 연결된 뉴스다. 추천·보유검토 입력으로 넘기기 전에 사람이 확인할 수 있는 최소 품질을 통과한 목록이다.
          숨긴 후보 {suppressedLowSignalCount}개는 삭제한 것이 아니라, 종목을 특정하지 못한 일반 뉴스라 기본 후보 목록에서 제외했다.
        </p>

        {directNewsCandidates.length > 0 ? (
          <div className="trace-grid">
            {directNewsCandidates.map((event) => (
              <CandidateCard event={event} key={`${event.event_id}-${event.ai_evidence_id}`} />
            ))}
          </div>
        ) : (
          <div className="empty-state">
            아직 직접 종목 뉴스 후보가 없다. 뉴스 묶음 근거는 <Link href="/intelligence">뉴스·AI 판단</Link>에서 확인한다.
          </div>
        )}
      </section>

      <section className="bento-card span-4 reveal delay-3" aria-labelledby="ai-evidence-macro-list-title">
        <div className="section-heading stacked-heading">
          <span>상위 흐름</span>
          <h2 id="ai-evidence-macro-list-title">종목 없이 먼저 보는 거시·테마 후보</h2>
        </div>
        <p className="relationship-empty">
          Fed, 금리, 유가, 소비 둔화처럼 특정 종목을 바로 찍기 어려운 뉴스는 이 섹션에 둔다.
          이 후보들은 상위 흐름으로 저장한 뒤 종목 노출도 규칙을 통해 관련 ETF·개별 종목으로 전파한다.
        </p>
        {macroNewsCandidates.length > 0 ? (
          <div className="trace-grid">
            {macroNewsCandidates.map((event) => (
              <CandidateCard event={event} key={`${event.event_id}-${event.ai_evidence_id}`} />
            ))}
          </div>
        ) : (
          <div className="empty-state">현재 상위 흐름 후보가 없다.</div>
        )}
      </section>
    </div>
  );
}
