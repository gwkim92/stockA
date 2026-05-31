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
  if (event.ai_evidence_type === "news_event_candidate_rejected" || event.quality_gate === "validator_blocked") {
    return "차단 후보";
  }
  return hasClassifiedSymbol(event) ? "직접 종목 후보" : "상위 흐름 후보";
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
        description: "종목 뉴스는 보유검토와 추천 점수의 직접 근거가 될 수 있다.",
      }
    : {
        label: "상위 흐름",
        value: koCode(event.theme_key),
        description: "거시·테마 뉴스는 관련 종목군으로 전파되는 상위 입력이다.",
      };
}

function candidatePurpose(event: NewsCandidateEvent) {
  if (event.ai_evidence_type === "news_event_candidate_rejected" || event.quality_gate === "validator_blocked") {
    return "AI가 후보를 만들었지만 검증 단계에서 추천 근거로 쓰기 어렵다고 판단했다.";
  }
  if (event.quality_gate === "low_signal_suppressed") {
    return "AI 후보는 존재하지만 신뢰도나 종목 연결이 약해 기본 추천 입력에서 제외한다.";
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

      <div className="relationship-panel" aria-label={`${event.title} AI 후보 연결`}>
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
  const candidates = data.events.filter((event) => event.ai_evidence_id);
  const newsCandidates = candidates.filter((event) => event.ai_evidence_type === "news_event_candidate");
  const directNewsCandidates = newsCandidates.filter(hasClassifiedSymbol);
  const macroNewsCandidates = newsCandidates.filter((event) => !hasClassifiedSymbol(event));
  const clusterEvidenceCount = allSummary.news_cluster_summary_count;
  const suppressedLowSignalCount = data.summary.suppressed_low_signal_candidate_count;
  const blockedCandidateCount = rejectedData.summary.event_count + suppressedData.summary.event_count;
  const translatedCandidateCount = newsCandidates.filter((event) => event.korean_title || event.korean_summary).length;
  const firstCandidateLink = candidates[0]?.ai_evidence_id ? evidenceHref(candidates[0].ai_evidence_id) : null;

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
          한 뉴스 단위로 AI가 구조화한 후보를 모았다. 종목이 없는 저신호 일반 뉴스는
          기본 후보에서 숨기고, 구조화 결과와 차단 후보는 별도 화면에서 확인한다.
        </p>
      </section>

      <section className="ai-evidence-command-panel reveal delay-1" aria-labelledby="ai-evidence-command-title">
        <div className="ai-evidence-command-lead">
          <span>AI 후보 작업대</span>
          <h2 id="ai-evidence-command-title">후보를 먼저 나누고, 상세에서 원천까지 추적한다.</h2>
          <p>
            이 화면은 AI가 만든 뉴스 후보를 분류하는 입구다. 직접 종목 후보는 보유·추천 근거 후보로,
            상위 흐름 후보는 테마 전파 입력으로, 차단 후보는 추천 입력 제외 항목으로 본다.
          </p>
        </div>
        <div className="ai-evidence-command-grid">
          <a className="ai-evidence-command-card ready" href="#accepted-candidates">
            <span>01</span>
            <small>직접 종목</small>
            <strong>{directNewsCandidates.length}개 후보</strong>
            <em>회사명·티커가 명확한 뉴스</em>
            <p>원문과 한국어 번역을 대조한 뒤 종목 상세, 추천 상세, 보유 thesis에서 실제 반영 위치를 확인한다.</p>
            <b>직접 후보 보기</b>
          </a>
          <a className="ai-evidence-command-card watch" href="#macro-candidates">
            <span>02</span>
            <small>상위 흐름</small>
            <strong>{macroNewsCandidates.length}개 후보</strong>
            <em>종목을 억지로 붙이지 않음</em>
            <p>금리, 정책, 유가, 산업 흐름은 먼저 테마로 저장하고 노출도 규칙으로 관련 종목에 전파한다.</p>
            <b>흐름 후보 보기</b>
          </a>
          <Link className="ai-evidence-command-card ready" href={"/ai-evidence/results" as Route}>
            <span>03</span>
            <small>통과 결과</small>
            <strong>{newsCandidates.length}개 구조화</strong>
            <em>한국어 번역 {translatedCandidateCount}/{newsCandidates.length}</em>
            <p>추천 입력 후보로 넘길 수 있는 구조화 결과를 종목, 테마, 방향, 신뢰도 기준으로 따로 확인한다.</p>
            <b>구조화 결과 보기</b>
          </Link>
          <Link
            className={blockedCandidateCount > 0 ? "ai-evidence-command-card block" : "ai-evidence-command-card ready"}
            href={"/ai-evidence/blocked" as Route}
          >
            <span>04</span>
            <small>차단·보류</small>
            <strong>{blockedCandidateCount}개 제외</strong>
            <em>저신호 {suppressedLowSignalCount} · 차단 {rejectedData.summary.event_count}</em>
            <p>추천 근거로 쓰지 않는 후보를 본다. 유효한 뉴스가 막혔다면 분류 체계와 종목 별칭을 보강한다.</p>
            <b>차단 후보 보기</b>
          </Link>
        </div>
        {firstCandidateLink ? (
          <div className="ai-evidence-command-footer">
            <span>상세 추적</span>
            <strong>후보 하나를 열면 원천 뉴스, 한국어 번역, AI 구조화 필드, validator 결과, 추천 연결을 한 화면에서 본다.</strong>
            <Link href={firstCandidateLink}>최신 후보 상세 열기</Link>
          </div>
        ) : null}
      </section>

      <section className="screen-switchboard reveal delay-1" aria-label="뉴스 처리 단계 바로가기">
        <Link className="screen-switch-card" href="/events">
          <span>01</span>
          <strong>수집 뉴스</strong>
          <small>원문 이벤트</small>
        </Link>
        <Link className="screen-switch-card" href={"/events/classification" as Route}>
          <span>02</span>
          <strong>1차 분류</strong>
          <small>자동 태그</small>
        </Link>
        <Link className="screen-switch-card active" href="/ai-evidence">
          <span>03</span>
          <strong>AI 분석 목록</strong>
          <small>후보 목록</small>
        </Link>
        <Link className="screen-switch-card" href={"/ai-evidence/results" as Route}>
          <span>04</span>
          <strong>구조화 결과</strong>
          <small>통과 결과</small>
        </Link>
        <Link className="screen-switch-card" href={"/ai-evidence/blocked" as Route}>
          <span>차단</span>
          <strong>차단 후보</strong>
          <small>추천 입력 제외</small>
        </Link>
      </section>

      <section className="status-rail compact-rail reveal delay-1" aria-label="뉴스 AI 후보 요약">
        <div className="rail-cell">
          <span>AI 연결 이벤트</span>
          <strong>{allSummary.ai_extracted_count}</strong>
          <small>AI 분석 후보와 뉴스 묶음 전체</small>
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
          <strong>{blockedCandidateCount}</strong>
          <small>저신호 {suppressedLowSignalCount} · 검증 차단 {rejectedData.summary.event_count}</small>
        </div>
      </section>

      <section className="ledger-guide reveal delay-2" aria-labelledby="ai-evidence-lane-guide-title">
        <div>
          <span>읽는 순서</span>
          <h2 id="ai-evidence-lane-guide-title">뉴스 AI 후보는 세 갈래로 나뉜다</h2>
        </div>
        <ol>
          <li>직접 종목 후보는 종목 상세, 보유검토, 추천 점수의 직접 근거 후보가 된다.</li>
          <li>상위 흐름 후보는 종목을 억지로 붙이지 않고 테마·거시 흐름으로 저장한 뒤 노출도 규칙으로 전파한다.</li>
          <li>차단 후보는 추천 입력에서 제외하고, 필요하면 분류 체계·종목 별칭·검증 규칙을 고친 뒤 다시 처리한다.</li>
        </ol>
      </section>

      <section className="bento-card span-4 reveal delay-2" id="accepted-candidates" aria-labelledby="ai-evidence-candidate-list-title">
        <div className="section-heading stacked-heading">
          <span>최신 후보</span>
          <h2 id="ai-evidence-candidate-list-title">직접 종목 뉴스 후보</h2>
        </div>
        <p className="relationship-empty">
          여기에 보이는 후보는 특정 종목에 직접 연결된 뉴스다. 자동 검증 기준을 통과해 추천·보유검토 입력 후보로 사용할 수 있다.
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

      <section className="bento-card span-4 reveal delay-3" id="macro-candidates" aria-labelledby="ai-evidence-macro-list-title">
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

      <section className="where-grid reveal delay-3" aria-label="AI 분석 후속 화면">
        <Link className="where-card" href={"/ai-evidence/results" as Route}>
          <span>결과</span>
          <strong>구조화 결과</strong>
          <p>통과한 후보를 종목·테마·방향·영향도 기준으로 확인한다.</p>
          <small>결과 화면 열기</small>
        </Link>
        <Link className="where-card" href={"/ai-evidence/blocked" as Route}>
          <span>차단</span>
          <strong>차단 후보 {blockedCandidateCount}개</strong>
          <p>검증 단계에서 추천 입력으로 넘기지 않은 후보와 이유를 확인한다.</p>
          <small>차단 화면 열기</small>
        </Link>
        <Link className="where-card" href="/intelligence">
          <span>묶음</span>
          <strong>뉴스 흐름 보드</strong>
          <p>여러 뉴스가 왜 같은 흐름으로 묶였는지 확인한다.</p>
          <small>흐름 보드 열기</small>
        </Link>
      </section>

    </div>
  );
}
