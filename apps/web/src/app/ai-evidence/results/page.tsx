import Link from "next/link";
import type { Route } from "next";

import {
  NewsEventCard,
  formatNewsPercent,
  isKnownNewsCode,
} from "@/components/news-event-card";
import { getAiNewsClusters, getEvents } from "@/lib/frontend-api";
import { koCode } from "@/lib/korean-labels";

export const dynamic = "force-dynamic";
export const metadata = { title: "구조화 결과" };

function formatClusterSymbols(symbols: string[]) {
  const known = symbols.filter(isKnownNewsCode);
  return known.length > 0 ? known.slice(0, 6).map(koCode).join(", ") : "시장/테마 뉴스";
}

export default async function StructuredResultsPage() {
  const [candidateResponse, clusterResponse] = await Promise.all([
    getEvents({ evidenceType: "news_event_candidate", limit: 80 }),
    getAiNewsClusters({ limit: 12 }),
  ]);
  const candidateData = candidateResponse.data;
  const clusterData = clusterResponse.data;
  const acceptedCandidates = candidateData.events.filter(
    (event) => event.ai_evidence_id && event.ai_evidence_type === "news_event_candidate",
  );
  const directCandidates = acceptedCandidates.filter((event) => isKnownNewsCode(event.symbol));
  const macroCandidates = acceptedCandidates.filter((event) => !isKnownNewsCode(event.symbol));

  return (
    <div className="pageStack structured-results-page">
      <section className="page-hero reveal" aria-labelledby="structured-results-title">
        <div>
          <div className="bento-badge">구조화 결과 · {candidateData.as_of_date}</div>
          <h1 className="page-title" id="structured-results-title">
            검증을 통과한 AI 결과만 따로 본다.
          </h1>
        </div>
        <p className="page-lede">
          이 화면은 AI가 무엇을 추출했고 어디에 연결했는지 보여준다. 수집 뉴스, 1차 태그 검수,
          차단 후보는 각각 별도 화면으로 분리했다.
        </p>
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
          <small>태그 검수</small>
        </Link>
        <Link className="screen-switch-card" href="/ai-evidence">
          <span>03</span>
          <strong>AI 분석 목록</strong>
          <small>후보 목록</small>
        </Link>
        <Link className="screen-switch-card active" href={"/ai-evidence/results" as Route}>
          <span>04</span>
          <strong>구조화 결과</strong>
          <small>통과 결과</small>
        </Link>
      </section>

      <section className="status-rail compact-rail reveal delay-1" aria-label="구조화 결과 요약">
        <article className="rail-cell">
          <span>통과 후보</span>
          <strong>{acceptedCandidates.length}</strong>
          <small>개별 뉴스 AI 결과</small>
        </article>
        <article className="rail-cell">
          <span>직접 종목</span>
          <strong>{directCandidates.length}</strong>
          <small>추천·보유검토 직접 근거</small>
        </article>
        <article className="rail-cell">
          <span>상위 흐름</span>
          <strong>{macroCandidates.length}</strong>
          <small>전파 대상 테마 뉴스</small>
        </article>
        <article className="rail-cell">
          <span>뉴스 묶음</span>
          <strong>{clusterData.summary.cluster_count}</strong>
          <small>흐름 보조 근거</small>
        </article>
        <article className="rail-cell">
          <span>최근 AI 실행</span>
          <strong className="rail-word-value">{koCode(clusterData.summary.latest_llm_invocation_status)}</strong>
          <small>
            {clusterData.summary.latest_llm_provider
              ? koCode(clusterData.summary.latest_llm_provider)
              : "분석 제공자 없음"}
          </small>
        </article>
      </section>

      <section className="bento-card span-4 reveal delay-2" id="accepted-results" aria-labelledby="structured-direct-title">
        <div className="section-heading stacked-heading">
          <span>직접 연결</span>
          <h2 id="structured-direct-title">종목에 바로 붙은 AI 구조화 결과</h2>
        </div>
        <p className="relationship-empty">
          이 목록은 추천·보유검토 근거로 바로 연결될 수 있다. 그래도 주문 결정은 하지 않으며,
          상세 화면에서 근거와 불확실성을 확인해야 한다.
        </p>
        <div className="news-row-list">
          {directCandidates.length > 0 ? (
            directCandidates.map((event) => (
              <NewsEventCard event={event} key={event.event_id} mode="result" />
            ))
          ) : (
            <div className="empty-state">현재 직접 종목 구조화 결과가 없다.</div>
          )}
        </div>
      </section>

      <section className="bento-card span-4 reveal delay-3" aria-labelledby="structured-macro-title">
        <div className="section-heading stacked-heading">
          <span>상위 흐름</span>
          <h2 id="structured-macro-title">종목을 억지로 붙이지 않은 AI 구조화 결과</h2>
        </div>
        <p className="relationship-empty">
          이 목록은 금리, 에너지, 양자컴퓨팅 정책 같은 흐름을 먼저 저장한다. 이후 노출도 테이블을 통해 관련 종목 영향으로 전파한다.
        </p>
        <div className="news-row-list">
          {macroCandidates.length > 0 ? (
            macroCandidates.map((event) => (
              <NewsEventCard event={event} key={event.event_id} mode="result" />
            ))
          ) : (
            <div className="empty-state">현재 상위 흐름 구조화 결과가 없다.</div>
          )}
        </div>
      </section>

      <section className="bento-card span-4 reveal delay-3" aria-labelledby="structured-cluster-title">
        <div className="section-heading stacked-heading">
          <span>뉴스 묶음</span>
          <h2 id="structured-cluster-title">같은 이야기로 묶인 구조화 결과</h2>
        </div>
        <div className="classification-grid">
          {clusterData.clusters.length > 0 ? (
            clusterData.clusters.map((cluster) => (
              <article className="classification-card" key={cluster.evidence_id}>
                <div className="trace-card-top">
                  <div>
                    <span className="metric-sub">
                      뉴스 {cluster.event_count}개 · 원천 {cluster.source_document_count}개 · {cluster.created_at}
                    </span>
                    <h2>{koCode(cluster.theme_key)}</h2>
                    <p className="cluster-story-context">
                      {cluster.story_label || cluster.theme_name} · {formatClusterSymbols(cluster.symbols)}
                    </p>
                  </div>
                  <span className="relation-pill">신뢰도 {formatNewsPercent(cluster.confidence)}</span>
                </div>
                <div className="relationship-panel">
                  <span>묶인 이유</span>
                  <div className="relationship-list">
                    {cluster.relation_reasons.slice(0, 3).map((reason) => (
                      <div className="relationship-chip" key={`${cluster.evidence_id}-${reason}`}>
                        <strong>{reason}</strong>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="btn-row">
                  <Link className="btn btn-primary" href={`/ai-evidence/${encodeURIComponent(cluster.evidence_id)}` as Route}>
                    묶음 상세
                  </Link>
                  <Link className="btn btn-secondary" href="/intelligence">
                    흐름 보드
                  </Link>
                </div>
              </article>
            ))
          ) : (
            <div className="empty-state">현재 저장된 뉴스 묶음 구조화 결과가 없다.</div>
          )}
        </div>
      </section>
    </div>
  );
}
