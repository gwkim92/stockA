import Link from "next/link";
import type { Route } from "next";

import {
  NewsEventCard,
  formatNewsPercent,
  isKnownNewsCode,
} from "@/components/news-event-card";
import { getAiNewsClusters, getEvents } from "@/lib/frontend-api";
import { koCode, koLabel } from "@/lib/korean-labels";

export const dynamic = "force-dynamic";
export const metadata = { title: "구조화 결과" };

function formatClusterSymbols(symbols: string[]) {
  const known = symbols.filter(isKnownNewsCode);
  return known.length > 0 ? known.slice(0, 6).map(koCode).join(", ") : "시장/테마 뉴스";
}

function formatClusterRelationReasons(reasons: string[]) {
  return reasons.length > 0 ? reasons.slice(0, 3) : ["same_theme"];
}

function formatLatestAiRunStatus(status: string | null | undefined) {
  if (!status || status === "not_run") {
    return "최근 AI 실행 이력 없음";
  }
  return `최근 AI 실행 ${koCode(status)}`;
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
  const latestAiRunStatus = formatLatestAiRunStatus(clusterData.summary.latest_llm_invocation_status);

  return (
    <div className="pageStack decision-page structured-results-page">
      <section className="decision-brief reveal" aria-labelledby="structured-results-title">
        <div className="decision-brief-main">
          <span className="decision-brief-kicker">구조화 결과 · {candidateData.as_of_date}</span>
          <h1 className="decision-brief-title" id="structured-results-title">
            추천 입력 후보는 {acceptedCandidates.length.toLocaleString("ko-KR")}개지만, 주문 결정은 아니다.
          </h1>
          <p className="decision-brief-copy">
            통과한 AI 결과도 바로 매수·매도 신호가 아니다. 직접 종목, 상위 흐름, 뉴스 묶음을 분리해서 보고
            추천 상세에서 가격·사이클·재무·가상 매매 검증과 다시 합친다.
          </p>
          <div className="decision-brief-meta" aria-label="구조화 결과 핵심 수치">
            <span>직접 종목 {directCandidates.length.toLocaleString("ko-KR")}개</span>
            <span>상위 흐름 {macroCandidates.length.toLocaleString("ko-KR")}개</span>
            <span>뉴스 묶음 {clusterData.summary.cluster_count.toLocaleString("ko-KR")}개</span>
            <span>{latestAiRunStatus}</span>
          </div>
        </div>
        <div className="decision-brief-grid">
          <a className="decision-card is-good" href="#accepted-results">
            <span>직접 종목</span>
            <strong>{directCandidates.length.toLocaleString("ko-KR")}개</strong>
            <small>회사명이나 티커가 명확한 뉴스다. 직접 연결이 과하지 않은지 원천과 대조한다.</small>
            <b>직접 결과</b>
          </a>
          <a className="decision-card is-watch" href="#macro-results">
            <span>상위 흐름</span>
            <strong>{macroCandidates.length.toLocaleString("ko-KR")}개</strong>
            <small>거시·테마 뉴스는 종목을 억지로 붙이지 않고 노출도로 전파한다.</small>
            <b>흐름 결과</b>
          </a>
          <a className="decision-card is-good" href="#cluster-results">
            <span>뉴스 묶음</span>
            <strong>{clusterData.summary.cluster_count.toLocaleString("ko-KR")}개</strong>
            <small>여러 뉴스가 같은 흐름인지 보여준다. 묶음이 틀리면 추천 근거 신뢰도도 낮아진다.</small>
            <b>묶음 보기</b>
          </a>
          <Link className="decision-card is-block" href={"/recommendations" as Route}>
            <span>실거래 상태</span>
            <strong>바로 주문 안 함</strong>
            <small>AI 결과는 추천 입력 후보일 뿐이며, 거래 안전 경계에서 다시 차단된다.</small>
            <b>추천 보기</b>
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
        <Link className="decision-flow-link" href="/ai-evidence">
          <span>03</span>
          <strong>AI 근거</strong>
          <small>후보 분리</small>
        </Link>
        <Link className="decision-flow-link is-active" href={"/ai-evidence/results" as Route}>
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

      <section className="ledger-section reveal delay-2" id="accepted-results" aria-labelledby="structured-direct-title">
        <div className="ledger-section-head">
          <div>
            <span className="ledger-section-kicker">직접 연결</span>
            <h2 className="ledger-section-title" id="structured-direct-title">종목에 바로 붙은 AI 구조화 결과</h2>
          </div>
          <p className="ledger-section-note">
            자동 검증을 통과했더라도 상세 화면에서 원천 뉴스와 불확실성을 함께 확인한다.
          </p>
        </div>
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

      <section className="ledger-section reveal delay-3" id="macro-results" aria-labelledby="structured-macro-title">
        <div className="ledger-section-head">
          <div>
            <span className="ledger-section-kicker">상위 흐름</span>
            <h2 className="ledger-section-title" id="structured-macro-title">종목을 억지로 붙이지 않은 AI 구조화 결과</h2>
          </div>
          <p className="ledger-section-note">
            금리, 에너지, 양자컴퓨팅 정책 같은 흐름은 먼저 테마로 저장하고 관련 종목 영향으로 전파한다.
          </p>
        </div>
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

      <section className="ledger-section reveal delay-3" id="cluster-results" aria-labelledby="structured-cluster-title">
        <div className="ledger-section-head">
          <div>
            <span className="ledger-section-kicker">뉴스 묶음</span>
            <h2 className="ledger-section-title" id="structured-cluster-title">같은 이야기로 묶인 구조화 결과</h2>
          </div>
          <p className="ledger-section-note">
            묶인 이유와 연결 대상이 맞는지 확인한다. 잘못 묶인 뉴스는 추천 근거 신뢰도를 떨어뜨린다.
          </p>
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
                    {formatClusterRelationReasons(cluster.relation_reasons).map((reason) => (
                      <div className="relationship-chip" key={`${cluster.evidence_id}-${reason}`}>
                        <strong>{koLabel(reason)}</strong>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="relationship-panel">
                  <span>추천에 연결되는 방식</span>
                  <div className="relationship-list">
                    <div className="relationship-chip">
                      <span>연결 대상</span>
                      <strong>{formatClusterSymbols(cluster.symbols)}</strong>
                      <small>종목이 없으면 시장·테마 흐름으로 먼저 남긴다.</small>
                    </div>
                    <div className="relationship-chip">
                      <span>사용 위치</span>
                      <strong>추천 보조 근거</strong>
                      <small>직접 뉴스와 상위 흐름 전파가 추천 상세에서 분리 표시된다.</small>
                    </div>
                    <div className="relationship-chip">
                      <span>다음 확인</span>
                      <strong>묶음 상세</strong>
                      <small>대표 뉴스, 원천 문서, AI 해석을 한국어로 확인한다.</small>
                    </div>
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
