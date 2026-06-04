import Link from "next/link";
import type { Route } from "next";

import { NewsEventCard } from "@/components/news-event-card";
import { getEvents } from "@/lib/frontend-api";
import type { EventListData } from "@/lib/types";

export const dynamic = "force-dynamic";
export const metadata = { title: "차단된 AI 구조화 항목" };

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

  return (
    <div className="pageStack decision-page blocked-evidence-page">
      <section className="decision-brief reveal" aria-labelledby="blocked-evidence-title">
        <div className="decision-brief-main">
          <span className="decision-brief-kicker">차단 항목 · {rejectedData.as_of_date}</span>
          <h1 className="decision-brief-title" id="blocked-evidence-title">
            추천 입력에서 제외된 AI 근거는 {blockedTotalCount.toLocaleString("ko-KR")}개다.
          </h1>
          <p className="decision-brief-copy">
            차단은 실패가 아니라 안전장치다. 잡음은 계속 제외하고, 유효한 뉴스가 분류 체계나 종목 별칭 부족으로
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
            <small>좋은 뉴스가 잘못 막혔을 때만 taxonomy와 ticker alias를 보강한다.</small>
            <b>분류 확인</b>
          </Link>
          <Link className="decision-card is-good" href={"/ai-evidence/results" as Route}>
            <span>통과 결과</span>
            <strong>분리 확인</strong>
            <small>추천 입력 후보는 차단 화면이 아니라 통과 결과에서 확인한다.</small>
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
          <strong>AI 근거</strong>
          <small>구조화 후보</small>
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

      <section className="ledger-section reveal delay-2" id="blocked-list" aria-labelledby="blocked-list-title">
        <div className="ledger-section-head">
          <div>
            <span className="ledger-section-kicker">차단/보류 원장</span>
            <h2 className="ledger-section-title" id="blocked-list-title">추천 근거로 쓰지 않는 AI 항목</h2>
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
