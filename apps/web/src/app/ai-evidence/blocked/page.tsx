import Link from "next/link";
import type { Route } from "next";

import { NewsEventCard } from "@/components/news-event-card";
import { getEvents } from "@/lib/frontend-api";

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
            추천 입력에서 제외된 AI 후보와 이유를 따로 본다.
          </h1>
        </div>
        <p className="page-lede">
          이 화면은 실패 목록이 아니라 안전장치다. 알 수 없는 종목·테마, 낮은 신뢰도, 종목 없는 저신호 뉴스는
          추천·보유검토 근거로 넘기지 않고, 필요한 경우 분류 체계나 종목 alias를 보강한다.
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
          <small>자동 태그</small>
        </Link>
        <Link className="screen-switch-card" href="/ai-evidence">
          <span>03</span>
          <strong>AI 분석 목록</strong>
          <small>후보 목록</small>
        </Link>
        <Link className="screen-switch-card" href={"/ai-evidence/results" as Route}>
          <span>04</span>
          <strong>구조화 결과</strong>
          <small>통과 결과</small>
        </Link>
        <Link className="screen-switch-card active" href={"/ai-evidence/blocked" as Route}>
          <span>차단</span>
          <strong>차단 후보</strong>
          <small>추천 입력 제외</small>
        </Link>
      </section>

      <section className="status-rail compact-rail reveal delay-1" aria-label="차단 후보 요약">
        <article className="rail-cell">
          <span>추천 입력 차단</span>
          <strong>{rejectedData.summary.event_count}</strong>
          <small>형식·분류 체계·신뢰도 기준</small>
        </article>
        <article className="rail-cell">
          <span>저신호 보류</span>
          <strong>{suppressedData.summary.event_count}</strong>
          <small>종목 없는 일반 뉴스</small>
        </article>
        <article className="rail-cell">
          <span>총 차단</span>
          <strong>{blockedEvents.length}</strong>
          <small>추천 입력 제외</small>
        </article>
        <article className="rail-cell">
          <span>상태</span>
          <strong className="rail-word-value">{blockedEvents.length > 0 ? "차단 기록 있음" : "차단 없음"}</strong>
          <small>추천 입력 제외 항목</small>
        </article>
      </section>

      <section className="cluster-decision-grid reveal delay-2" aria-label="차단 후보 읽는 법">
        <article className="cluster-decision-cell">
          <span>왜 제외됐나</span>
          <strong>추천 품질 방어</strong>
          <p>알 수 없는 종목, 낮은 신뢰도, 약한 뉴스 신호는 추천 점수와 보유검토에 넣지 않는다.</p>
        </article>
        <article className="cluster-decision-cell">
          <span>복구 가능한가</span>
          <strong>분류 체계 보강 후보</strong>
          <p>좋은 뉴스가 taxonomy나 ticker alias 부족으로 막혔다면 규칙을 보강하고 재실행한다.</p>
        </article>
        <article className="cluster-decision-cell cluster-decision-final">
          <span>현재 처리</span>
          <strong>자동 제외 상태</strong>
          <p>차단 후보는 원천과 AI 출력만 보존한다. 추천 입력에는 들어가지 않는다.</p>
        </article>
      </section>

      <section className="ledger-guide reveal delay-2" aria-labelledby="blocked-guide-title">
        <div>
          <span>읽는 순서</span>
          <h2 id="blocked-guide-title">차단 후보는 이렇게 처리한다</h2>
        </div>
        <ol>
          <li>잡음으로 판단된 뉴스는 추천·보유검토 입력에서 계속 제외한다.</li>
          <li>유효한 뉴스가 분류 체계 부족으로 막힌 경우에는 taxonomy, theme, ticker alias를 보강한다.</li>
          <li>보강 후 같은 배치를 재실행해 차단 후보가 통과 결과로 이동하는지 확인한다.</li>
        </ol>
      </section>

      <section className="bento-card span-4 reveal delay-2" aria-labelledby="blocked-list-title">
        <div className="section-heading stacked-heading">
          <span>차단/보류 목록</span>
          <h2 id="blocked-list-title">AI가 만들었지만 추천 근거로 쓰지 않는 후보</h2>
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
