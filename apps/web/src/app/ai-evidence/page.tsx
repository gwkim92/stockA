import Link from "next/link";
import type { Route } from "next";

import { getEvents } from "@/lib/frontend-api";
import { koCode, koLabel } from "@/lib/korean-labels";

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

export default async function AiEvidenceIndexPage() {
  const response = await getEvents({ limit: 50 });
  const data = response.data;
  const candidates = data.events.filter((event) => event.ai_evidence_id);
  const newsCandidates = candidates.filter((event) => event.ai_evidence_type === "news_event_candidate");

  return (
    <div className="pageStack">
      <section className="page-hero reveal" aria-labelledby="ai-evidence-index-title">
        <div>
          <div className="bento-badge">개별 뉴스 후보 분석 • {data.as_of_date}</div>
          <h1 className="page-title" id="ai-evidence-index-title">
            AI가 해석한 뉴스 후보를 한 곳에서 본다.
          </h1>
        </div>
        <p className="page-lede">
          이 화면은 RSS 뉴스 중 AI 구조화가 붙은 항목만 모은 입구다. 각 카드를 열면 AI가 어떤 테마, 종목,
          영향 방향, 불확실성을 추출했는지 확인할 수 있다.
        </p>
      </section>

      <section className="status-rail compact-rail reveal delay-1" aria-label="뉴스 AI 후보 요약">
        <div className="rail-cell">
          <span>AI 연결 이벤트</span>
          <strong>{candidates.length}</strong>
          <small>상세 근거로 이동 가능한 뉴스</small>
        </div>
        <div className="rail-cell">
          <span>개별 뉴스 후보</span>
          <strong>{newsCandidates.length}</strong>
          <small>테마·종목·방향 추출 대상</small>
        </div>
        <div className="rail-cell">
          <span>원천 문서</span>
          <strong>{data.summary.source_document_count}</strong>
          <small>뉴스와 공시의 출처</small>
        </div>
        <div className="rail-cell">
          <span>품질 기준</span>
          <strong className="rail-word-value">검토</strong>
          <small>AI는 근거만 남기고 주문은 하지 않는다</small>
        </div>
      </section>

      <section className="bento-card span-4 reveal delay-2" aria-labelledby="ai-evidence-candidate-list-title">
        <div className="section-heading stacked-heading">
          <span>최신 후보</span>
          <h2 id="ai-evidence-candidate-list-title">개별 뉴스 후보 분석 목록</h2>
        </div>

        {candidates.length > 0 ? (
          <div className="trace-grid">
            {candidates.map((event) => {
              const evidenceLink = evidenceHref(event.ai_evidence_id as string);
              const documentLink = sourceDocumentHref(event.source_document_id);
              const isCandidate = event.ai_evidence_type === "news_event_candidate";

              return (
                <article className="trace-card" key={`${event.event_id}-${event.ai_evidence_id}`}>
                  <div className="trace-card-top">
                    <div>
                      <span className="metric-sub">
                        {koCode(event.symbol)} • {koCode(event.event_type)} • {event.event_at}
                      </span>
                      <h3>{koLabel(event.title)}</h3>
                    </div>
                    <span className="relation-pill">{isCandidate ? "개별 후보" : koCode(event.ai_evidence_type)}</span>
                  </div>

                  <div className="evidence-strip">
                    <span>분석 상태</span>
                    <strong>{koCode(event.ai_evidence_provider)} · {formatPercent(event.ai_evidence_confidence)}</strong>
                    <p>
                      {isCandidate
                        ? "AI가 뉴스 한 건을 테마, 종목, 방향, 불확실성으로 구조화했다."
                        : "여러 뉴스를 같은 테마 흐름으로 묶은 보조 증거다."}
                    </p>
                  </div>

                  <div className="relationship-panel" aria-label={`${event.title} AI 후보 연결`}>
                    <span>추천 판단에 들어가기 전 확인할 내용</span>
                    <div className="relationship-list">
                      <div className="relationship-chip">
                        <span>테마</span>
                        <strong>{koCode(event.theme_key)}</strong>
                        <small>같은 테마 흐름과 사이클 상태를 함께 본다.</small>
                      </div>
                      <div className="relationship-chip">
                        <span>방향</span>
                        <strong>{koCode(event.impact_direction)}</strong>
                        <small>영향도 {Math.round(event.impact_score * 1000) / 10}% · {koCode(event.quality_gate)}</small>
                      </div>
                      <div className="relationship-chip">
                        <span>다음 화면</span>
                        <strong>상세 근거</strong>
                        <small>추출 필드, 원천 청크, 검증 메모를 확인한다.</small>
                      </div>
                    </div>
                  </div>

                  <div className="btn-row">
                    <Link className="btn btn-primary" href={evidenceLink}>
                      AI 후보 상세
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
            })}
          </div>
        ) : (
          <div className="empty-state">
            아직 AI 구조화가 붙은 뉴스 후보가 없다. 뉴스 수집과 뉴스 AI 분석 배치가 실행되면 이 목록에 표시된다.
          </div>
        )}
      </section>
    </div>
  );
}
