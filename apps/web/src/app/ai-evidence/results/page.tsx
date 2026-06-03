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
  const latestAiRunStatus = clusterData.summary.latest_llm_invocation_status
    ? `최근 AI 실행 ${koCode(clusterData.summary.latest_llm_invocation_status)}`
    : "최근 AI 실행 없음";

  return (
    <div className="pageStack structured-results-page">
      <section className="page-hero reveal" aria-labelledby="structured-results-title">
        <div>
          <div className="bento-badge">구조화 결과 · {candidateData.as_of_date}</div>
          <h1 className="page-title" id="structured-results-title">
            추천 입력으로 넘어갈 수 있는 AI 결과를 따로 본다.
          </h1>
        </div>
        <p className="page-lede">
          이 화면은 AI가 어떤 종목·테마·방향을 추출했고, 추천·보유 상태 근거로 넘길 수 있는지 보여준다.
          수집 뉴스, 1차 자동 태그, 차단 후보는 각각 별도 화면으로 분리했다.
        </p>
      </section>

      <section className="ai-evidence-command-panel reveal delay-1" aria-labelledby="structured-command-title">
        <div className="ai-evidence-command-lead">
          <span>통과 결과 판정판</span>
          <h2 id="structured-command-title">AI 통과 결과를 투자 입력 후보로만 본다.</h2>
          <p>
            자동 검증을 통과한 결과라도 바로 추천이나 주문이 아니다. 직접 종목 뉴스, 상위 흐름,
            뉴스 묶음을 분리해서 보고, 추천 상세에서 가격·사이클·재무·가상 매매 검증과 다시 합친다.
          </p>
        </div>
        <div className="ai-evidence-command-grid">
          <a className="ai-evidence-command-card ready" href="#accepted-results">
            <span>01</span>
            <small>직접 종목</small>
            <strong>{directCandidates.length}개 결과</strong>
            <em>종목 상세·추천 상세 연결 후보</em>
            <p>회사명이나 티커가 명확한 뉴스다. 원천 뉴스와 한국어 번역을 열어 직접 연결이 과하지 않은지 본다.</p>
            <b>직접 결과 보기</b>
          </a>
          <a className="ai-evidence-command-card watch" href="#macro-results">
            <span>02</span>
            <small>상위 흐름</small>
            <strong>{macroCandidates.length}개 결과</strong>
            <em>거시·테마 전파 입력</em>
            <p>금리, 정책, 유가, 산업 뉴스는 종목을 억지로 붙이지 않고 흐름으로 저장한 뒤 노출도로 전파한다.</p>
            <b>흐름 결과 보기</b>
          </a>
          <a className="ai-evidence-command-card ready" href="#cluster-results">
            <span>03</span>
            <small>뉴스 묶음</small>
            <strong>{clusterData.summary.cluster_count}개 묶음</strong>
            <em>같은 이야기의 근거 묶음</em>
            <p>여러 뉴스가 같은 흐름을 말하는지 본다. 묶음이 틀리면 추천 근거 신뢰도도 낮아진다.</p>
            <b>묶음 결과 보기</b>
          </a>
          <Link className="ai-evidence-command-card block" href={"/recommendations" as Route}>
            <span>04</span>
            <small>추천 경계</small>
            <strong>바로 주문 안 함</strong>
            <em>{latestAiRunStatus}</em>
            <p>AI 통과 결과는 추천 점수의 입력 후보일 뿐이다. 실제 판단은 추천 상세와 거래 안전 경계에서 다시 막는다.</p>
            <b>추천 경계 보기</b>
          </Link>
        </div>
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
        <Link className="screen-switch-card" href="/ai-evidence">
          <span>03</span>
          <strong>AI 근거 목록</strong>
          <small>후보 목록</small>
        </Link>
        <Link className="screen-switch-card active" href={"/ai-evidence/results" as Route}>
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

      <section className="status-rail compact-rail reveal delay-1" aria-label="구조화 결과 요약">
        <article className="rail-cell">
          <span>통과 후보</span>
          <strong>{acceptedCandidates.length}</strong>
          <small>추천 입력 가능 후보</small>
        </article>
        <article className="rail-cell">
          <span>직접 종목</span>
          <strong>{directCandidates.length}</strong>
          <small>추천·보유 상태 직접 근거</small>
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

      <section className="cluster-decision-grid reveal delay-2" aria-label="구조화 결과 읽는 법">
        <article className="cluster-decision-cell">
          <span>직접 종목 뉴스</span>
          <strong>종목에 바로 연결</strong>
          <p>회사명·티커가 명확한 뉴스다. 종목 상세, 추천 근거, 보유 상태 입력으로 이어질 수 있다.</p>
        </article>
        <article className="cluster-decision-cell">
          <span>상위 흐름 뉴스</span>
          <strong>거시·테마로 먼저 저장</strong>
          <p>금리, 유가, 정책, 산업 사이클 뉴스다. 종목 미분류가 오류가 아니라 전파 전 단계다.</p>
        </article>
        <article className="cluster-decision-cell">
          <span>뉴스 묶음</span>
          <strong>같은 이야기의 근거 묶음</strong>
          <p>여러 기사와 원천 문서가 같은 흐름을 말하는지 보여준다. 하나의 기사보다 흐름 신뢰도를 높인다.</p>
        </article>
        <article className="cluster-decision-cell cluster-decision-final">
          <span>추천 연결</span>
          <strong>바로 주문하지 않음</strong>
          <p>통과 결과는 추천 점수와 보유 thesis의 입력이다. 주문은 거래 안전 조건을 따로 통과해야 한다.</p>
        </article>
      </section>

      <section className="bento-card span-4 reveal delay-2" id="accepted-results" aria-labelledby="structured-direct-title">
        <div className="section-heading stacked-heading">
          <span>직접 연결</span>
          <h2 id="structured-direct-title">종목에 바로 붙은 AI 구조화 결과</h2>
        </div>
        <p className="relationship-empty">
          이 목록은 자동 검증을 통과해 추천·보유 상태 근거 후보로 바로 연결될 수 있다.
          주문 결정은 만들지 않으며, 상세 화면에서 원천 뉴스와 불확실성을 함께 보여준다.
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

      <section className="bento-card span-4 reveal delay-3" id="macro-results" aria-labelledby="structured-macro-title">
        <div className="section-heading stacked-heading">
          <span>상위 흐름</span>
          <h2 id="structured-macro-title">종목을 억지로 붙이지 않은 AI 구조화 결과</h2>
        </div>
        <p className="relationship-empty">
          이 목록은 금리, 에너지, 양자컴퓨팅 정책 같은 흐름을 먼저 저장한다.
          특정 종목을 억지로 붙이지 않고, 이후 노출도 테이블을 통해 관련 종목 영향으로 전파한다.
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

      <section className="bento-card span-4 reveal delay-3" id="cluster-results" aria-labelledby="structured-cluster-title">
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
