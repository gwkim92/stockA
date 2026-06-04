import Link from "next/link";
import type { Route } from "next";

import { NewsTitleBlock } from "@/components/news-title-block";
import { getEvents } from "@/lib/frontend-api";
import { koCode } from "@/lib/korean-labels";
import type { EventListData } from "@/lib/types";

export const dynamic = "force-dynamic";
export const metadata = { title: "뉴스 AI 구조화 항목" };

function formatPercent(value: number | null) {
  if (value === null) {
    return "신뢰도 미제공";
  }
  return `신뢰도 ${Math.round(value * 1000) / 10}%`;
}

function safeCount(value: unknown) {
  return typeof value === "number" && Number.isFinite(value) ? value : 0;
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
  if (event.ai_evidence_type === "news_event_candidate_rejected" || event.quality_gate === "validator_blocked") {
    return "차단 항목";
  }
  return hasClassifiedSymbol(event) ? "직접 종목 항목" : "상위 흐름 항목";
}

function candidateDetailButtonLabel(event: NewsCandidateEvent) {
  if (event.ai_evidence_type === "news_event_candidate_rejected" || event.quality_gate === "validator_blocked") {
    return "차단 근거 상세";
  }
  return hasClassifiedSymbol(event) ? "종목 연결 근거" : "흐름 연결 근거";
}

function candidatePrimaryChip(event: NewsCandidateEvent) {
  return hasClassifiedSymbol(event)
    ? {
        label: "직접 종목",
        value: koCode(event.symbol),
        description: "종목 뉴스는 보유 상태 판단과 추천 점수의 직접 근거가 될 수 있다.",
      }
    : {
        label: "상위 흐름",
        value: koCode(event.theme_key),
        description: "거시·테마 뉴스는 관련 종목군으로 전파되는 상위 입력이다.",
      };
}

function candidatePurpose(event: NewsCandidateEvent) {
  if (event.ai_evidence_type === "news_event_candidate_rejected" || event.quality_gate === "validator_blocked") {
    return "AI가 구조화 항목을 만들었지만 자동 검증 단계에서 추천 근거로 쓰기 어렵다고 분류했다.";
  }
  if (event.quality_gate === "low_signal_suppressed") {
    return "AI 구조화 항목은 존재하지만 신뢰도나 종목 연결이 약해 기본 추천 입력에서 제외한다.";
  }
  if (hasClassifiedSymbol(event)) {
    return "AI가 뉴스 한 건을 특정 종목, 테마, 방향, 불확실성으로 구조화했다.";
  }
  return "AI가 종목을 억지로 붙이지 않고 거시·테마 흐름으로 구조화했다. 이후 노출도 규칙으로 관련 종목에 전파된다.";
}

function validationOutcome(event: NewsCandidateEvent) {
  if (event.ai_evidence_type === "news_event_candidate_rejected" || event.quality_gate === "validator_blocked") {
    return "차단";
  }
  if (event.quality_gate === "low_signal_suppressed") {
    return "저신호 보류";
  }
  return "자동 검증 통과";
}

function CandidateCard({ event }: { event: NewsCandidateEvent }) {
  const primaryChip = candidatePrimaryChip(event);
  const evidenceLink = event.ai_evidence_id ? evidenceHref(event.ai_evidence_id) : null;
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
            koreanTitle={event.korean_title}
            koreanSummary={event.korean_summary}
            translationConfidence={event.translation_confidence}
            symbol={event.symbol}
            themeKey={event.theme_key}
            impactDirection={event.impact_direction}
            impactScore={event.impact_score}
          />
        </div>
        <span className="relation-pill">{candidateKindLabel(event)}</span>
      </div>

      <div className="evidence-strip">
        <span>검증 결과</span>
        <strong>{validationOutcome(event)} · {koCode(event.ai_evidence_provider)} · {formatPercent(event.ai_evidence_confidence)}</strong>
        <p>{candidatePurpose(event)}</p>
      </div>

      <div className="relationship-panel" aria-label={`${event.title} AI 구조화 항목 연결`}>
        <span>추천 입력으로 이동하는 근거 경로</span>
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
            <small>AI 추출값, 한국어 요약, 원천 문서가 함께 보인다.</small>
          </div>
        </div>
      </div>

      <div className="btn-row">
        {evidenceLink ? (
          <Link className="btn btn-primary" href={evidenceLink}>
            {candidateDetailButtonLabel(event)}
          </Link>
        ) : null}
        <Link className="btn btn-secondary" href="/events">
          수집 뉴스
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
  const [response, allEventsResponse, rejectedResponse, suppressedResponse] = await Promise.all([
    getEvents({ evidenceType: "news_event_candidate", limit: 50 }),
    getEvents({ limit: 1 }),
    getEvents({ evidenceType: "news_event_candidate_rejected", limit: 30 }),
    getEvents({ evidenceType: "news_event_candidate_suppressed", limit: 30 }),
  ]);
  const data = response.data;
  const allSummary = allEventsResponse.data.summary;
  const rejectedData = rejectedResponse.data;
  const suppressedData = suppressedResponse.data;
  const allSummaryFields = allSummary as typeof allSummary & Record<string, unknown>;
  const dataSummaryFields = data.summary as typeof data.summary & Record<string, unknown>;
  const rejectedSummaryFields = rejectedData.summary as typeof rejectedData.summary & Record<string, unknown>;
  const suppressedSummaryFields = suppressedData.summary as typeof suppressedData.summary & Record<string, unknown>;
  const candidates = data.events.filter((event) => event.ai_evidence_id);
  const newsCandidates = candidates.filter((event) => event.ai_evidence_type === "news_event_candidate");
  const directNewsCandidates = newsCandidates.filter(hasClassifiedSymbol);
  const macroNewsCandidates = newsCandidates.filter((event) => !hasClassifiedSymbol(event));
  const aiExtractedCount = safeCount(allSummaryFields.ai_extracted_count);
  const clusterEvidenceCount = safeCount(allSummaryFields.news_cluster_summary_count);
  const suppressedLowSignalCount = safeCount(dataSummaryFields.suppressed_low_signal_candidate_count);
  const rejectedEventCount = safeCount(rejectedSummaryFields.event_count);
  const suppressedEventCount = safeCount(suppressedSummaryFields.event_count);
  const blockedCandidateCount = rejectedEventCount + suppressedEventCount;
  const translatedCandidateCount = newsCandidates.filter((event) => event.korean_title || event.korean_summary).length;
  const firstCandidateLink = candidates[0]?.ai_evidence_id ? evidenceHref(candidates[0].ai_evidence_id) : null;

  return (
    <div className="pageStack decision-page">
      <section className="decision-brief reveal" aria-labelledby="ai-evidence-index-title">
        <div className="decision-brief-main">
          <span className="decision-brief-kicker">뉴스 AI 근거 · {data.as_of_date}</span>
          <h1 className="decision-brief-title" id="ai-evidence-index-title">
            AI 근거는 직접 종목 {directNewsCandidates.length.toLocaleString("ko-KR")}개, 상위 흐름 {macroNewsCandidates.length.toLocaleString("ko-KR")}개로 나눠 본다.
          </h1>
          <p className="decision-brief-copy">
            여기서는 AI가 만든 후보를 한 화면에 다 붓지 않는다. 종목에 바로 붙는 근거, 거시·테마로 먼저 남길 근거,
            추천 입력에서 제외할 근거를 분리해서 본다.
          </p>
          <div className="decision-brief-meta" aria-label="뉴스 AI 근거 핵심 수치">
            <span>AI 연결 {aiExtractedCount.toLocaleString("ko-KR")}건</span>
            <span>한국어 {translatedCandidateCount.toLocaleString("ko-KR")}/{newsCandidates.length.toLocaleString("ko-KR")}</span>
            <span>뉴스 묶음 {clusterEvidenceCount.toLocaleString("ko-KR")}개</span>
            <span>차단·보류 {blockedCandidateCount.toLocaleString("ko-KR")}개</span>
          </div>
        </div>
        <div className="decision-brief-grid">
          <a className="decision-card is-good" href="#accepted-candidates">
            <span>직접 종목</span>
            <strong>{directNewsCandidates.length.toLocaleString("ko-KR")}개</strong>
            <small>회사명·티커가 명확한 뉴스다. 종목 상세와 추천 근거에서 다시 확인한다.</small>
            <b>직접 근거</b>
          </a>
          <a className="decision-card is-watch" href="#macro-candidates">
            <span>상위 흐름</span>
            <strong>{macroNewsCandidates.length.toLocaleString("ko-KR")}개</strong>
            <small>금리·정책·유가 같은 뉴스는 종목을 억지로 붙이지 않고 흐름으로 전파한다.</small>
            <b>흐름 근거</b>
          </a>
          <Link className="decision-card is-good" href={"/ai-evidence/results" as Route}>
            <span>통과 결과</span>
            <strong>{newsCandidates.length.toLocaleString("ko-KR")}개</strong>
            <small>추천 입력 후보로 볼 수 있는 구조화 결과만 따로 확인한다.</small>
            <b>결과 보기</b>
          </Link>
          <Link className={blockedCandidateCount > 0 ? "decision-card is-block" : "decision-card is-good"} href={"/ai-evidence/blocked" as Route}>
            <span>차단·보류</span>
            <strong>{blockedCandidateCount.toLocaleString("ko-KR")}개</strong>
            <small>저신호 {suppressedLowSignalCount.toLocaleString("ko-KR")}개 · 검증 차단 {rejectedEventCount.toLocaleString("ko-KR")}개</small>
            <b>차단 보기</b>
          </Link>
        </div>
      </section>

      <section className="decision-flow-nav reveal delay-1" aria-label="뉴스 처리 단계">
        <Link className="decision-flow-link" href="/events">
          <span>01</span>
          <strong>수집 뉴스</strong>
          <small>원문 이벤트</small>
        </Link>
        <Link className="decision-flow-link" href={"/events/classification" as Route}>
          <span>02</span>
          <strong>1차 분류</strong>
          <small>자동 태그</small>
        </Link>
        <Link className="decision-flow-link is-active" href="/ai-evidence">
          <span>03</span>
          <strong>AI 근거</strong>
          <small>후보 분리</small>
        </Link>
        <Link className="decision-flow-link" href={"/ai-evidence/results" as Route}>
          <span>04</span>
          <strong>통과 결과</strong>
          <small>추천 입력 후보</small>
        </Link>
        <Link className="decision-flow-link" href={"/ai-evidence/blocked" as Route}>
          <span>차단</span>
          <strong>차단 항목</strong>
          <small>입력 제외</small>
        </Link>
      </section>

      <section className="ledger-section reveal delay-2" id="accepted-candidates" aria-labelledby="ai-evidence-candidate-list-title">
        <div className="ledger-section-head">
          <div>
            <span className="ledger-section-kicker">직접 종목</span>
            <h2 className="ledger-section-title" id="ai-evidence-candidate-list-title">종목에 바로 붙은 AI 근거</h2>
          </div>
          <p className="ledger-section-note">
            원천과 한국어 번역을 대조한 뒤 종목 상세, 추천 상세, 보유 논리에서 실제 반영 위치를 확인한다.
          </p>
        </div>

        {directNewsCandidates.length > 0 ? (
          <div className="trace-grid">
            {directNewsCandidates.map((event) => (
              <CandidateCard event={event} key={`${event.event_id}-${event.ai_evidence_id}`} />
            ))}
          </div>
        ) : (
          <div className="empty-state">
            아직 직접 종목 뉴스 구조화 항목이 없다. 뉴스 묶음 근거는 <Link href="/intelligence">뉴스·AI 근거</Link>에서 확인한다.
          </div>
        )}
      </section>

      <section className="ledger-section reveal delay-3" id="macro-candidates" aria-labelledby="ai-evidence-macro-list-title">
        <div className="ledger-section-head">
          <div>
            <span className="ledger-section-kicker">상위 흐름</span>
            <h2 className="ledger-section-title" id="ai-evidence-macro-list-title">종목을 억지로 붙이지 않은 AI 근거</h2>
          </div>
          <p className="ledger-section-note">
            금리, 유가, 정책, 산업 사이클 뉴스는 테마로 저장한 뒤 노출도 규칙으로 관련 종목에 전파한다.
          </p>
        </div>
        {macroNewsCandidates.length > 0 ? (
          <div className="trace-grid">
            {macroNewsCandidates.map((event) => (
              <CandidateCard event={event} key={`${event.event_id}-${event.ai_evidence_id}`} />
            ))}
          </div>
        ) : (
          <div className="empty-state">현재 상위 흐름 항목이 없다.</div>
        )}
      </section>

      {firstCandidateLink ? (
        <section className="where-grid reveal delay-3" aria-label="AI 상세 추적">
          <Link className="where-card" href={firstCandidateLink}>
            <span>상세</span>
            <strong>최신 항목 추적</strong>
            <p>원천 뉴스, 한국어 번역, AI 구조화 필드, 검증 결과, 추천 연결을 한 화면에서 본다.</p>
            <small>최신 상세 열기</small>
          </Link>
          <Link className="where-card" href={"/ai-evidence/results" as Route}>
            <span>결과</span>
            <strong>통과 결과</strong>
            <p>추천 입력 후보만 종목·테마·방향 기준으로 확인한다.</p>
            <small>결과 화면 열기</small>
          </Link>
          <Link className="where-card" href={"/ai-evidence/blocked" as Route}>
            <span>차단</span>
            <strong>차단·보류</strong>
            <p>추천 입력으로 쓰지 않는 항목과 이유를 따로 확인한다.</p>
            <small>차단 화면 열기</small>
          </Link>
        </section>
      ) : null}

    </div>
  );
}
