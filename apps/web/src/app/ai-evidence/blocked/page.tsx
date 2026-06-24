import Link from "next/link";
import type { Route } from "next";

import { NewsEventCard } from "@/components/news-event-card";
import { getEvents } from "@/lib/frontend-api";
import type { EventListData } from "@/lib/types";
import { EvidencePathWorkbench, type EvidencePathStep } from "../_components/evidence-path-workbench";

export const dynamic = "force-dynamic";
export const metadata = { title: "차단된 뉴스 근거" };

type NewsEvent = EventListData["events"][number];

function isValidatorBlockedEvent(event: NewsEvent) {
  return event.ai_evidence_type === "news_event_candidate_rejected" || event.quality_gate === "validator_blocked";
}

function isLowSignalSuppressedEvent(event: NewsEvent) {
  return event.ai_evidence_type === "news_event_candidate_suppressed" || event.quality_gate === "low_signal_suppressed";
}

function uniqueEvents(events: NewsEvent[]) {
  const seen = new Set<string>();
  return events.filter((event) => {
    const key = `${event.event_id}:${event.ai_evidence_id ?? ""}:${event.quality_gate}`;
    if (seen.has(key)) {
      return false;
    }
    seen.add(key);
    return true;
  });
}

export default async function BlockedAiEvidencePage() {
  const [rejectedResponse, suppressedResponse] = await Promise.all([
    getEvents({ evidenceType: "news_event_candidate_rejected", limit: 80 }),
    getEvents({ evidenceType: "news_event_candidate_suppressed", limit: 80 }),
  ]);
  const rejectedData = rejectedResponse.data;
  const suppressedData = suppressedResponse.data;
  const rejectedEvents = uniqueEvents(rejectedData.events.filter(isValidatorBlockedEvent));
  const suppressedEvents = uniqueEvents(
    suppressedData.events
      .filter((event) => isLowSignalSuppressedEvent(event) && !isValidatorBlockedEvent(event))
      .map((event) => ({ ...event, quality_gate: "low_signal_suppressed" })),
  );
  const blockedEvents = uniqueEvents([...rejectedEvents, ...suppressedEvents]);
  const blockedTotalCount = blockedEvents.length;
  const translatedBlockedCount = blockedEvents.filter((event) => event.korean_title || event.korean_summary).length;
  const sourceLinkedCount = blockedEvents.filter((event) => event.source_document_id).length;
  const pathSteps: EvidencePathStep[] = [
    {
      index: "01",
      label: "원천 보존",
      value: `원천 ${sourceLinkedCount.toLocaleString("ko-KR")}개`,
      body: "차단돼도 원천 뉴스는 남긴다. 나중에 분류 체계나 종목 별칭 보강이 필요한지 확인하기 위해서다.",
      tone: sourceLinkedCount > 0 ? "ready" : "watch",
      href: "/events",
      cta: "수집 뉴스 보기",
    },
    {
      index: "02",
      label: "한국어 요약",
      value: `${translatedBlockedCount.toLocaleString("ko-KR")}개`,
      body: "차단 항목도 한국어 제목·요약으로 잡음인지, 좋은 뉴스가 잘못 막힌 것인지 구분한다.",
      tone: translatedBlockedCount > 0 ? "ready" : "watch",
    },
    {
      index: "03",
      label: "근거 후보",
      value: `${blockedTotalCount.toLocaleString("ko-KR")}개`,
      body: "근거 후보가 만들어졌어도 품질 기준을 통과하지 못하면 추천 근거로 넘기지 않는다.",
      tone: blockedTotalCount > 0 ? "blocked" : "ready",
      href: "#blocked-list",
      cta: "목록 보기",
    },
    {
      index: "04",
      label: "차단 사유",
      value: `검증 ${rejectedEvents.length} · 저신호 ${suppressedEvents.length}`,
      body: "원문 근거 없는 종목, 알 수 없는 테마, 낮은 신뢰도, 일반 시장 잡음은 추천 입력에서 제외한다.",
      tone: blockedTotalCount > 0 ? "blocked" : "ready",
    },
    {
      index: "05",
      label: "후속 조치",
      value: "보강 또는 제외",
      body: "좋은 뉴스가 잘못 막힌 경우만 분류 체계와 ticker alias를 보강한다. 그 외 항목은 계속 제외한다.",
      tone: "watch",
      href: "/events/classification",
      cta: "분류 보강 보기",
    },
  ];

  return (
    <div className="pageStack decision-page blocked-evidence-page">
      <section className="decision-brief reveal" aria-labelledby="blocked-evidence-title">
        <div className="decision-brief-main">
          <span className="decision-brief-kicker">차단 항목 · {rejectedData.as_of_date}</span>
          <h1 className="decision-brief-title" id="blocked-evidence-title">
            추천 입력에서 제외된 뉴스 근거는 {blockedTotalCount.toLocaleString("ko-KR")}개다.
          </h1>
          <p className="decision-brief-copy">
            차단은 장애가 아니라 안전장치다. 잡음은 계속 제외하고, 유효한 뉴스가 분류 체계나 종목 별칭 부족으로
            막힌 경우만 보강 대상으로 넘긴다.
          </p>
          <div className="decision-brief-meta" aria-label="차단 항목 핵심 수치">
            <span>검증 차단 {rejectedEvents.length.toLocaleString("ko-KR")}개</span>
            <span>저신호 보류 {suppressedEvents.length.toLocaleString("ko-KR")}개</span>
            <span>상태 {blockedTotalCount > 0 ? "차단 기록 있음" : "차단 없음"}</span>
          </div>
        </div>
        <div className="decision-brief-grid">
          <a className="decision-card is-block" href="#blocked-list">
            <span>계속 제외</span>
            <strong>{rejectedEvents.length.toLocaleString("ko-KR")}개</strong>
            <small>알 수 없는 종목·테마, 낮은 신뢰도, 근거 부족 항목이다.</small>
            <b>목록 보기</b>
          </a>
          <a className="decision-card is-watch" href="#blocked-list">
            <span>저신호 보류</span>
            <strong>{suppressedEvents.length.toLocaleString("ko-KR")}개</strong>
            <small>종목 없는 일반 뉴스다. 삭제하지 않지만 추천 입력으로 쓰지 않는다.</small>
            <b>보류 보기</b>
          </a>
          <Link className="decision-card is-watch" href={"/events/classification" as Route}>
            <span>보강 후보</span>
            <strong>분류·별칭</strong>
            <small>좋은 뉴스가 잘못 막혔을 때만 분류 체계와 종목 별칭을 보강한다.</small>
            <b>분류 보기</b>
          </Link>
          <Link className="decision-card is-good" href={"/ai-evidence/results" as Route}>
            <span>통과 결과</span>
            <strong>통과 항목</strong>
            <small>추천 입력 후보는 차단 화면이 아니라 통과 결과에 모은다.</small>
            <b>결과 보기</b>
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
          <strong>투자 근거</strong>
          <small>직접/상위 후보</small>
        </Link>
        <Link className="decision-flow-link" href={"/ai-evidence/results" as Route}>
          <span>04</span>
          <strong>통과 결과</strong>
          <small>추천 입력 후보</small>
        </Link>
        <Link className="decision-flow-link is-active" href={"/ai-evidence/blocked" as Route}>
          <span>차단</span>
          <strong>차단 항목</strong>
          <small>입력 제외</small>
        </Link>
      </section>

      <EvidencePathWorkbench
        eyebrow="차단 항목을 읽는 순서"
        title="차단은 오류 목록이 아니라 추천 입력에서 제외한 이유다"
        summary="핵심은 제외 건수를 세는 것이 아니다. 원천 뉴스가 남아 있는지, 한국어로 대조 가능한지, 왜 품질 기준을 통과하지 못했는지, 보강할 항목인지 계속 제외할 항목인지 판단한다."
        verdict={`품질 차단 ${rejectedEvents.length.toLocaleString("ko-KR")}개 · 저신호 보류 ${suppressedEvents.length.toLocaleString("ko-KR")}개 · 자동 주문 영향 없음.`}
        verdictTone={blockedTotalCount > 0 ? "blocked" : "ready"}
        steps={pathSteps}
      />

      <section className="ledger-section reveal delay-2" id="blocked-list" aria-labelledby="blocked-list-title">
        <div className="ledger-section-head">
          <div>
            <span className="ledger-section-kicker">차단/보류 원장</span>
            <h2 className="ledger-section-title" id="blocked-list-title">추천 근거로 쓰지 않는 뉴스 항목</h2>
          </div>
          <p className="ledger-section-note">
            전체 {blockedTotalCount.toLocaleString("ko-KR")}개 중 최신 {blockedEvents.length.toLocaleString("ko-KR")}개를 표시한다. 유효한 뉴스가 잘못 막혔으면 분류 체계와 종목 별칭을 보강한 뒤 같은 배치를 다시 실행한다.
          </p>
        </div>
        <div className="news-row-list">
          {blockedEvents.length > 0 ? (
            blockedEvents.map((event) => (
              <NewsEventCard event={event} key={`${event.event_id}-${event.ai_evidence_id ?? event.quality_gate}`} mode="blocked" />
            ))
          ) : (
            <div className="empty-state">현재 차단 또는 보류된 항목이 없다.</div>
          )}
        </div>
      </section>
    </div>
  );
}
