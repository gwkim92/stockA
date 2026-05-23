import Link from "next/link";
import type { Route } from "next";

import { NewsEventCard, formatNewsPercent } from "@/components/news-event-card";
import { getEvents } from "@/lib/frontend-api";

export const dynamic = "force-dynamic";
export const metadata = { title: "수집 뉴스" };

export default async function EventsPage() {
  const response = await getEvents({ limit: 80 });
  const data = response.data;
  const linkedCount = data.events.filter((event) => event.ai_evidence_id).length;
  const unlinkedCount = data.events.length - linkedCount;
  const latestEvent = data.events[0];

  return (
    <div className="pageStack news-ledger-page">
      <section className="page-hero reveal" aria-labelledby="news-ledger-title">
        <div>
          <div className="bento-badge">수집 뉴스 · {data.as_of_date}</div>
          <h1 className="page-title" id="news-ledger-title">
            들어온 뉴스와 공시를 시간순으로 확인한다.
          </h1>
        </div>
        <p className="page-lede">
          이 화면은 투자 결론을 내리는 곳이 아니다. 원문 제목, 수집 시각, 1차 태그, AI 연결 여부를 확인하고
          분류나 AI 결과가 이상한 뉴스만 다음 화면에서 검토한다.
        </p>
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
          <small>Codex OAuth 후보 확인</small>
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

      <section className="bento-card span-4 reveal delay-2" aria-labelledby="news-ledger-list-title">
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
          <p>Codex OAuth가 구조화한 후보만 따로 확인한다.</p>
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
