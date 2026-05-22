import Link from "next/link";
import type { Route } from "next";

import { NewsEventCard } from "@/components/news-event-card";
import { getEvents } from "@/lib/frontend-api";
import { koCode } from "@/lib/korean-labels";

export const dynamic = "force-dynamic";
export const metadata = { title: "차단 후보" };

export default async function BlockedAiEvidencePage() {
  const [rejectedResponse, suppressedResponse] = await Promise.all([
    getEvents({ evidenceType: "news_event_candidate_rejected", limit: 80 }),
    getEvents({ evidenceType: "news_event_candidate_suppressed", limit: 80 }),
  ]);
  const rejectedData = rejectedResponse.data;
  const suppressedData = suppressedResponse.data;
  const blockedEvents = [
    ...rejectedData.events,
    ...suppressedData.events.map((event) => ({ ...event, quality_gate: "low_signal_suppressed" })),
  ];

  return (
    <div className="pageStack blocked-evidence-page">
      <section className="page-hero reveal" aria-labelledby="blocked-evidence-title">
        <div>
          <div className="bento-badge">차단 후보 · {rejectedData.as_of_date}</div>
          <h1 className="page-title" id="blocked-evidence-title">
            추천 입력으로 쓰면 위험한 AI 후보를 따로 본다.
          </h1>
        </div>
        <p className="page-lede">
          이 화면은 실패 목록이 아니라 안전장치다. 알 수 없는 종목·테마, 낮은 confidence, 종목 없는 저신호 뉴스는
          추천·보유검토 근거로 넘기지 않는다.
        </p>
      </section>

      <section className="screen-switchboard reveal delay-1" aria-label="뉴스 처리 단계 바로가기">
        <Link className="screen-switch-card" href="/events">
          <span>01</span>
          <strong>수집 원장</strong>
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
        <Link className="screen-switch-card active" href={"/ai-evidence/blocked" as Route}>
          <span>차단</span>
          <strong>차단 후보</strong>
          <small>추천 입력 제외</small>
        </Link>
      </section>

      <section className="status-rail compact-rail reveal delay-1" aria-label="차단 후보 요약">
        <article className="rail-cell">
          <span>validator 차단</span>
          <strong>{rejectedData.summary.event_count}</strong>
          <small>schema/ontology/confidence gate</small>
        </article>
        <article className="rail-cell">
          <span>저신호 보류</span>
          <strong>{suppressedData.summary.event_count}</strong>
          <small>종목 없는 일반 top story</small>
        </article>
        <article className="rail-cell">
          <span>총 차단</span>
          <strong>{blockedEvents.length}</strong>
          <small>추천 입력 제외</small>
        </article>
        <article className="rail-cell">
          <span>상태</span>
          <strong className="rail-word-value">{blockedEvents.length > 0 ? "검토 가능" : "차단 없음"}</strong>
          <small>{koCode(rejectedData.filters.evidence_type)}</small>
        </article>
      </section>

      <section className="ledger-guide reveal delay-2" aria-labelledby="blocked-guide-title">
        <div>
          <span>읽는 순서</span>
          <h2 id="blocked-guide-title">차단 후보는 세 가지를 확인한다</h2>
        </div>
        <ol>
          <li>정말 차단해야 하는 잡음인지 본다.</li>
          <li>좋은 뉴스인데 taxonomy나 종목 alias가 부족해서 막혔는지 본다.</li>
          <li>후자라면 분류 체계나 validator 규칙을 고친다.</li>
        </ol>
      </section>

      <section className="bento-card span-4 reveal delay-2" aria-labelledby="blocked-list-title">
        <div className="section-heading stacked-heading">
          <span>차단/보류 목록</span>
          <h2 id="blocked-list-title">AI가 만들었지만 추천 입력으로 넘기지 않은 후보</h2>
        </div>
        <div className="news-row-list">
          {blockedEvents.length > 0 ? (
            blockedEvents.map((event) => (
              <NewsEventCard event={event} key={`${event.event_id}-${event.ai_evidence_id ?? event.quality_gate}`} mode="blocked" />
            ))
          ) : (
            <div className="empty-state">현재 차단 또는 보류된 후보가 없다.</div>
          )}
        </div>
      </section>
    </div>
  );
}
