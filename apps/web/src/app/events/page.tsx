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
  const eventCommandCards = [
    {
      index: "01",
      label: "수집 원장",
      title:
        data.summary.event_count > 0
          ? `${data.summary.event_count.toLocaleString("ko-KR")}건 수집`
          : "수집 뉴스 없음",
      metric: `원천 ${data.summary.source_document_count.toLocaleString("ko-KR")}개 · 번역 ${translatedCount.toLocaleString("ko-KR")}건`,
      body:
        data.summary.event_count > 0
          ? "RSS·공시에서 들어온 원문 이벤트다. 먼저 한국어 제목과 원천 문서가 실제로 있는지 확인한다."
          : "현재 필터 기준 수집된 뉴스가 없다. 데이터 수집 상태를 먼저 확인한다.",
      href: "#news-ledger-list",
      cta: "원장 보기",
      tone: data.summary.event_count > 0 ? "ready" : "block",
    },
    {
      index: "02",
      label: "1차 분류",
      title:
        data.summary.themes_represented > 0
          ? `${data.summary.themes_represented.toLocaleString("ko-KR")}개 테마`
          : "테마 없음",
      metric: `직접 종목 ${directInstrumentCount.toLocaleString("ko-KR")}건 · 상위 흐름 ${macroOrThemeCount.toLocaleString("ko-KR")}건`,
      body:
        data.summary.themes_represented > 0
          ? "종목 뉴스와 거시·테마 뉴스를 분리해서 본다. 거시 뉴스에 종목이 없는 것은 오류가 아닐 수 있다."
          : "아직 1차 테마 분류가 없다. 분류 화면에서 누락 이유를 확인한다.",
      href: "/events/classification",
      cta: "분류 보기",
      tone: data.summary.themes_represented > 0 ? "watch" : "block",
    },
    {
      index: "03",
      label: "AI 연결",
      title: linkedCount > 0 ? `${linkedCount.toLocaleString("ko-KR")}건 연결` : "AI 분석 전",
      metric: `후보 ${data.summary.news_event_candidate_count.toLocaleString("ko-KR")}건 · 묶음 ${data.summary.news_cluster_summary_count.toLocaleString("ko-KR")}건`,
      body:
        linkedCount > 0
          ? "AI evidence가 연결된 뉴스는 구조화 상세에서 원문, 번역, 판단 근거, 추천 연결 여부를 추적한다."
          : "수집은 됐지만 아직 AI 분석 근거가 연결되지 않았다. 추천 입력으로 쓰기 전 단계다.",
      href: "/ai-evidence",
      cta: "AI 분석 보기",
      tone: linkedCount > 0 ? "ready" : "watch",
    },
    {
      index: "04",
      label: "차단·보류",
      title:
        blockedOrSuppressedCount > 0
          ? `${blockedOrSuppressedCount.toLocaleString("ko-KR")}건 확인`
          : "차단 없음",
      metric: `저신호 ${data.summary.suppressed_low_signal_candidate_count.toLocaleString("ko-KR")}건 · 미검토 ${data.summary.unreviewed_event_count.toLocaleString("ko-KR")}건`,
      body:
        blockedOrSuppressedCount > 0
          ? "validator 차단이나 저신호 보류 뉴스는 추천 근거로 쓰면 안 된다. 차단 화면에서 이유를 확인한다."
          : "현재 목록에서는 차단·저신호 후보가 두드러지지 않는다. 그래도 AI 결과 화면에서 validator 상태를 확인한다.",
      href: "/ai-evidence/blocked",
      cta: "차단 보기",
      tone: blockedOrSuppressedCount > 0 ? "block" : "ready",
    },
  ];

  return (
    <div className="pageStack news-ledger-page">
      <section className="page-hero reveal" aria-labelledby="news-ledger-title">
        <div>
          <div className="bento-badge">수집 뉴스 · {data.as_of_date}</div>
          <h1 className="page-title" id="news-ledger-title">
            뉴스가 들어온 뒤, 어디까지 해석됐는지 먼저 본다.
          </h1>
        </div>
        <p className="page-lede">
          이 화면은 투자 결론이나 주문을 내리는 곳이 아니다. 수집 원장, 1차 분류, AI 분석 연결,
          validator 차단 여부를 분리해서 보고 이상한 뉴스만 다음 화면에서 추적한다.
        </p>
      </section>

      <section className="events-command-panel reveal delay-1" aria-labelledby="events-command-title">
        <div className="events-command-lead">
          <span>뉴스 이벤트 판정판</span>
          <h2 id="events-command-title">원문이 들어왔는지보다, 판단 입력으로 쓸 수 있는지 본다.</h2>
          <p>
            최신 이벤트 {latestEvent ? latestEvent.event_at : "없음"} · 기준일 {data.as_of_date}.
            뉴스는 원장, 분류, AI 구조화, validator 통과를 거친 뒤에만 추천 근거 후보가 된다.
          </p>
        </div>
        <div className="events-command-grid">
          {eventCommandCards.map((card) => (
            <a className={`events-command-card ${card.tone}`} href={card.href} key={card.index}>
              <span>{card.index}</span>
              <small>{card.label}</small>
              <strong>{card.title}</strong>
              <em>{card.metric}</em>
              <p>{card.body}</p>
              <b>{card.cta}</b>
            </a>
          ))}
        </div>
      </section>

      <section className="screen-switchboard reveal delay-1" aria-label="뉴스 처리 단계 바로가기">
        <Link className="screen-switch-card active" href="/events">
          <span>01</span>
          <strong>수집 뉴스</strong>
          <small>원문 이벤트가 들어왔는지 확인</small>
        </Link>
        <Link className="screen-switch-card" href={"/events/classification" as Route}>
          <span>02</span>
          <strong>1차 분류</strong>
          <small>종목·테마·방향 태그 확인</small>
        </Link>
        <Link className="screen-switch-card" href="/ai-evidence">
          <span>03</span>
          <strong>AI 분석 목록</strong>
          <small>AI 후보 확인</small>
        </Link>
        <Link className="screen-switch-card" href={"/ai-evidence/results" as Route}>
          <span>04</span>
          <strong>구조화 결과</strong>
          <small>통과한 근거만 확인</small>
        </Link>
      </section>

      <section className="status-rail compact-rail reveal delay-1" aria-label="수집 뉴스 요약">
        <article className="rail-cell">
          <span>수집 뉴스</span>
          <strong>{data.summary.event_count}</strong>
          <small>현재 필터 기준</small>
        </article>
        <article className="rail-cell">
          <span>원천 문서</span>
          <strong>{data.summary.source_document_count}</strong>
          <small>RSS/공시 문서 수</small>
        </article>
        <article className="rail-cell">
          <span>AI 연결</span>
          <strong>{linkedCount}</strong>
          <small>현재 목록 내 연결 수</small>
        </article>
        <article className="rail-cell">
          <span>AI 전</span>
          <strong>{unlinkedCount}</strong>
          <small>수집됐지만 아직 판단 입력은 아님</small>
        </article>
        <article className="rail-cell">
          <span>테마 수</span>
          <strong>{data.summary.themes_represented}</strong>
          <small>1차 분류 기준</small>
        </article>
      </section>

      <section className="ledger-guide reveal delay-2" aria-labelledby="news-ledger-guide-title">
        <div>
          <span>읽는 순서</span>
          <h2 id="news-ledger-guide-title">수집 뉴스는 세 가지만 보면 된다</h2>
        </div>
        <ol>
          <li>제목이 실제 투자 관련 뉴스인지 확인한다.</li>
          <li>종목·테마·방향 태그가 말이 되는지 본다.</li>
          <li>AI 근거가 있으면 상세로 들어가고, 없으면 아직 분석 전으로 둔다.</li>
        </ol>
        <p>
          최신 수집 뉴스 기준 첫 이벤트는 {latestEvent ? `"${latestEvent.title}"` : "아직 없다"}이며,
          영향도는 {latestEvent ? formatNewsPercent(latestEvent.impact_score) : "미측정"}다.
        </p>
      </section>

      <section className="bento-card span-4 reveal delay-2" id="news-ledger-list" aria-labelledby="news-ledger-list-title">
        <div className="section-heading stacked-heading">
          <span>최신 수집 뉴스</span>
          <h2 id="news-ledger-list-title">수집된 뉴스와 이벤트</h2>
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
          <strong>AI 분석 목록</strong>
          <p>AI가 구조화한 후보만 따로 확인한다.</p>
          <small>분석 목록 열기</small>
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
