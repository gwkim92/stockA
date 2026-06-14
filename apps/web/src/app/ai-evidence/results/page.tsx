import Link from "next/link";
import type { Route } from "next";

import {
  NewsEventCard,
  formatNewsPercent,
  isKnownNewsCode,
} from "@/components/news-event-card";
import { getAiNewsClusters, getEvents } from "@/lib/frontend-api";
import { koCode, koLabel } from "@/lib/korean-labels";
import { EvidencePathWorkbench, type EvidencePathStep } from "../_components/evidence-path-workbench";

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

function formatCoverage(done: number, total: number) {
  if (total <= 0) {
    return "대상 없음";
  }
  return `${done.toLocaleString("ko-KR")}/${total.toLocaleString("ko-KR")}`;
}

function clusterTranslatedCount(cluster: Awaited<ReturnType<typeof getAiNewsClusters>>["data"]["clusters"][number]) {
  return cluster.source_documents.filter((document) => document.korean_title || document.korean_summary).length
    || cluster.events.filter((event) => event.korean_title || event.korean_summary).length;
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
  const translatedCandidateCount = acceptedCandidates.filter((event) => event.korean_title || event.korean_summary).length;
  const sourceDocumentCount = candidateData.summary.source_document_count + clusterData.summary.source_document_count;
  const pathSteps: EvidencePathStep[] = [
    {
      index: "01",
      label: "원천 뉴스",
      value: `원천 ${sourceDocumentCount.toLocaleString("ko-KR")}개`,
      body: "통과 결과도 원천 뉴스나 문서가 있어야 추천 입력 후보로 볼 수 있다.",
      tone: sourceDocumentCount > 0 ? "ready" : "watch",
      href: "/events",
      cta: "수집 뉴스 보기",
    },
    {
      index: "02",
      label: "한국어 번역",
      value: `후보 ${formatCoverage(translatedCandidateCount, acceptedCandidates.length)}`,
      body: "영어 원문만 보지 않도록 한국어 제목·요약이 있는 항목을 우선 확인한다.",
      tone: translatedCandidateCount > 0 ? "ready" : "watch",
    },
    {
      index: "03",
      label: "AI 구조화",
      value: `직접 ${directCandidates.length} · 흐름 ${macroCandidates.length}`,
      body: "종목 뉴스와 거시·테마 뉴스를 분리한다. 거시 뉴스에 억지로 티커를 붙이지 않는다.",
      tone: acceptedCandidates.length > 0 ? "ready" : "watch",
      href: "#accepted-results",
      cta: "결과 나눠 보기",
    },
    {
      index: "04",
      label: "자동 검증",
      value: "통과 항목",
      body: "이 화면에는 추천 입력 후보만 모은다. 차단·보류 항목은 별도 화면에서 봐야 한다.",
      tone: "ready",
      href: "/ai-evidence/blocked",
      cta: "차단 항목 보기",
    },
    {
      index: "05",
      label: "추천·주문 경계",
      value: "주문 아님",
      body: "AI 결과는 가격, 사이클, 재무, thesis, 페이퍼 검증과 합쳐진 뒤에도 자동 주문으로 가지 않는다.",
      tone: "watch",
      href: "/recommendations",
      cta: "추천 경계 보기",
    },
  ];

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

      <EvidencePathWorkbench
        eyebrow="통과 결과를 읽는 순서"
        title="AI가 통과시킨 뉴스도 바로 추천이나 주문이 아니다"
        summary="먼저 원천과 번역을 보고, AI가 종목 뉴스와 상위 흐름 뉴스를 어떻게 나눴는지 확인한다. 그 다음 추천 상세에서 다른 근거와 합쳐졌는지 본다."
        verdict={`현재 통과 후보 ${acceptedCandidates.length.toLocaleString("ko-KR")}개 · 주문 경계는 계속 읽기 전용이다.`}
        verdictTone={acceptedCandidates.length > 0 ? "ready" : "watch"}
        steps={pathSteps}
      />

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
                <ol className="evidence-mini-path" aria-label={`${cluster.story_label || cluster.theme_name} 묶음 판단 경로`}>
                  <li>
                    <span>원천</span>
                    <strong>{cluster.source_document_count.toLocaleString("ko-KR")}개</strong>
                  </li>
                  <li>
                    <span>번역</span>
                    <strong>{formatCoverage(clusterTranslatedCount(cluster), cluster.source_documents.length || cluster.events.length)}</strong>
                  </li>
                  <li>
                    <span>구조화</span>
                    <strong>{koCode(cluster.extraction_run.provider)}</strong>
                  </li>
                  <li>
                    <span>연결</span>
                    <strong>{formatClusterSymbols(cluster.symbols)}</strong>
                  </li>
                </ol>
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
