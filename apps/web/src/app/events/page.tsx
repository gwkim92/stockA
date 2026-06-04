import Link from "next/link";
import type { Route } from "next";

import { NewsEventCard, formatNewsPercent } from "@/components/news-event-card";
import { getEvents } from "@/lib/frontend-api";

export const dynamic = "force-dynamic";
export const metadata = { title: "수집 뉴스" };

const UNCLASSIFIED_SYMBOL_KEYS = new Set(["", "UNKNOWN", "UNCLASSIFIED"]);

export default async function EventsPage() {
  const response = await getEvents({ limit: 80 });
  const data = response.data;
  const linkedCount = data.events.filter((event) => event.ai_evidence_id).length;
  const unlinkedCount = data.events.length - linkedCount;
  const translatedCount = data.events.filter((event) => event.korean_title || event.korean_summary).length;
  const directInstrumentCount = data.events.filter((event) => !UNCLASSIFIED_SYMBOL_KEYS.has(event.symbol)).length;
  const macroOrThemeCount = data.events.length - directInstrumentCount;
  const blockedOrSuppressedCount = data.events.filter(
    (event) =>
      event.quality_gate === "validator_blocked"
      || event.quality_gate === "low_signal_suppressed"
      || event.ai_evidence_type === "news_event_candidate_rejected",
  ).length;
  const latestEvent = data.events[0];

  return (
    <div className="pageStack decision-page news-ledger-page">
      <section className="decision-brief reveal" aria-labelledby="news-ledger-title">
        <div className="decision-brief-main">
          <span className="decision-brief-kicker">수집 뉴스 · {data.as_of_date}</span>
          <h1 className="decision-brief-title" id="news-ledger-title">
            오늘 들어온 뉴스는 {linkedCount.toLocaleString("ko-KR")}건이 AI 근거와 연결됐다.
          </h1>
          <p className="decision-brief-copy">
            먼저 볼 것은 기사 목록 전체가 아니라 처리 상태다. 수집, 1차 분류, AI 연결, 차단 여부를 확인한 뒤
            필요한 뉴스만 원장으로 내려가서 본다.
          </p>
          <div className="decision-brief-meta" aria-label="수집 뉴스 핵심 수치">
            <span>최신 {latestEvent ? latestEvent.event_at : "없음"}</span>
            <span>원천 {data.summary.source_document_count.toLocaleString("ko-KR")}개</span>
            <span>번역 {translatedCount.toLocaleString("ko-KR")}건</span>
            <span>AI 대기 {unlinkedCount.toLocaleString("ko-KR")}건</span>
          </div>
        </div>
        <div className="decision-brief-grid">
          <a className={data.summary.event_count > 0 ? "decision-card is-good" : "decision-card is-block"} href="#news-ledger-list">
            <span>수집</span>
            <strong>{data.summary.event_count.toLocaleString("ko-KR")}건</strong>
            <small>RSS·공시에서 들어온 원문 이벤트다. 목록은 아래 원장에서 확인한다.</small>
            <b>원장 보기</b>
          </a>
          <Link className="decision-card is-watch" href={"/events/classification" as Route}>
            <span>1차 분류</span>
            <strong>{data.summary.themes_represented.toLocaleString("ko-KR")}개 테마</strong>
            <small>직접 종목 {directInstrumentCount.toLocaleString("ko-KR")}건 · 상위 흐름 {macroOrThemeCount.toLocaleString("ko-KR")}건</small>
            <b>분류 보기</b>
          </Link>
          <Link className={linkedCount > 0 ? "decision-card is-good" : "decision-card is-watch"} href="/ai-evidence">
            <span>AI 연결</span>
            <strong>{linkedCount.toLocaleString("ko-KR")}건</strong>
            <small>AI가 구조화한 뉴스는 원천, 번역, 판단 필드, 추천 연결을 상세에서 추적한다.</small>
            <b>근거 보기</b>
          </Link>
          <Link className={blockedOrSuppressedCount > 0 ? "decision-card is-block" : "decision-card is-good"} href={"/ai-evidence/blocked" as Route}>
            <span>차단·보류</span>
            <strong>{blockedOrSuppressedCount.toLocaleString("ko-KR")}건</strong>
            <small>검증 차단이나 저신호 뉴스는 추천 입력으로 쓰지 않는다.</small>
            <b>차단 보기</b>
          </Link>
        </div>
      </section>

      <section className="decision-flow-nav reveal delay-1" aria-label="뉴스 처리 단계">
        <Link className="decision-flow-link is-active" href="/events">
          <span>01</span>
          <strong>수집 뉴스</strong>
          <small>원문 이벤트</small>
        </Link>
        <Link className="decision-flow-link" href={"/events/classification" as Route}>
          <span>02</span>
          <strong>1차 분류</strong>
          <small>종목·테마·방향</small>
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
      </section>

      <section className="ledger-section reveal delay-2" id="news-ledger-list" aria-labelledby="news-ledger-list-title">
        <div className="ledger-section-head">
          <div>
            <span className="ledger-section-kicker">원장</span>
            <h2 className="ledger-section-title" id="news-ledger-list-title">수집된 뉴스와 이벤트</h2>
          </div>
          <p className="ledger-section-note">
            최신 첫 이벤트는 {latestEvent ? `"${latestEvent.title}"` : "아직 없다"} · 영향도 {latestEvent ? formatNewsPercent(latestEvent.impact_score) : "미측정"}.
          </p>
        </div>
        <div className="news-row-list">
          {data.events.length > 0 ? (
            data.events.map((event) => (
              <NewsEventCard event={event} key={event.event_id} mode="ledger" />
            ))
          ) : (
            <div className="empty-state">현재 수집된 뉴스가 비어 있다.</div>
          )}
        </div>
      </section>

      <section className="where-grid reveal delay-3" aria-label="다음 확인 화면">
        <Link className="where-card" href={"/events/classification" as Route}>
          <span>다음</span>
          <strong>1차 분류 태그</strong>
          <p>수집 뉴스에 붙은 종목·테마·방향이 맞는지 테마별로 확인한다.</p>
          <small>분류 화면 열기</small>
        </Link>
        <Link className="where-card" href="/ai-evidence">
          <span>다음</span>
          <strong>AI 근거 목록</strong>
          <p>AI가 구조화한 근거 후보만 따로 확인한다.</p>
          <small>근거 목록 열기</small>
        </Link>
        <Link className="where-card" href={"/ai-evidence/blocked" as Route}>
          <span>검증</span>
          <strong>차단 후보</strong>
          <p>추천 입력으로 쓰면 안 되는 후보가 왜 막혔는지 본다.</p>
          <small>차단 목록 열기</small>
        </Link>
      </section>
    </div>
  );
}
