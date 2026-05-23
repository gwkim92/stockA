import Link from "next/link";
import type { Route } from "next";

import {
  NewsEventCard,
  formatNewsPercent,
  isKnownNewsCode,
  type NewsEventRow,
} from "@/components/news-event-card";
import { getEvents } from "@/lib/frontend-api";
import { koCode } from "@/lib/korean-labels";

export const dynamic = "force-dynamic";
export const metadata = { title: "1차 분류 태그" };

type ThemeGroup = {
  themeKey: string;
  themeName: string;
  events: NewsEventRow[];
  symbols: Set<string>;
  supportive: number;
  riskReview: number;
  watch: number;
};

function buildThemeGroups(events: NewsEventRow[]) {
  const groups = new Map<string, ThemeGroup>();
  for (const event of events) {
    const key = event.theme_key || "UNCLASSIFIED";
    const group = groups.get(key) ?? {
      themeKey: key,
      themeName: event.theme_name,
      events: [],
      symbols: new Set<string>(),
      supportive: 0,
      riskReview: 0,
      watch: 0,
    };

    group.events.push(event);
    if (isKnownNewsCode(event.symbol)) {
      group.symbols.add(event.symbol);
    }
    if (event.impact_direction === "supportive") {
      group.supportive += 1;
    } else if (event.impact_direction === "risk_review") {
      group.riskReview += 1;
    } else {
      group.watch += 1;
    }
    groups.set(key, group);
  }

  return Array.from(groups.values()).sort((left, right) => {
    if (right.events.length !== left.events.length) {
      return right.events.length - left.events.length;
    }
    return left.themeKey.localeCompare(right.themeKey);
  });
}

function directionSummary(group: ThemeGroup) {
  return [
    group.supportive > 0 ? `우호 ${group.supportive}` : null,
    group.riskReview > 0 ? `리스크 ${group.riskReview}` : null,
    group.watch > 0 ? `관찰 ${group.watch}` : null,
  ].filter(Boolean).join(" · ") || "방향 미분류";
}

export default async function ClassificationPage() {
  const response = await getEvents({ limit: 100 });
  const data = response.data;
  const groups = buildThemeGroups(data.events);
  const directSymbolCount = data.events.filter((event) => isKnownNewsCode(event.symbol)).length;
  const macroOnlyCount = data.events.length - directSymbolCount;
  const strongestEvent = [...data.events].sort((left, right) => right.impact_score - left.impact_score)[0];

  return (
    <div className="pageStack classification-page">
      <section className="page-hero reveal" aria-labelledby="classification-title">
        <div>
          <div className="bento-badge">1차 분류 태그 · {data.as_of_date}</div>
          <h1 className="page-title" id="classification-title">
            AI 전에 붙은 종목·테마·방향 태그를 검수한다.
          </h1>
        </div>
        <p className="page-lede">
          이 화면은 수집된 뉴스에 처음 붙은 해석만 따로 보는 곳이다. 테마가 이상하거나 종목이 잘못 붙은
          뉴스는 여기서 먼저 발견하고, AI 구조화 결과와 비교한다.
        </p>
      </section>

      <section className="screen-switchboard reveal delay-1" aria-label="뉴스 처리 단계 바로가기">
        <Link className="screen-switch-card" href="/events">
          <span>01</span>
          <strong>수집 뉴스</strong>
          <small>원문 이벤트 확인</small>
        </Link>
        <Link className="screen-switch-card active" href={"/events/classification" as Route}>
          <span>02</span>
          <strong>1차 분류</strong>
          <small>태그와 방향 검수</small>
        </Link>
        <Link className="screen-switch-card" href="/ai-evidence">
          <span>03</span>
          <strong>AI 분석 목록</strong>
          <small>AI 후보 확인</small>
        </Link>
        <Link className="screen-switch-card" href={"/ai-evidence/results" as Route}>
          <span>04</span>
          <strong>구조화 결과</strong>
          <small>통과 결과 확인</small>
        </Link>
      </section>

      <section className="status-rail compact-rail reveal delay-1" aria-label="1차 분류 요약">
        <article className="rail-cell">
          <span>테마</span>
          <strong>{groups.length}</strong>
          <small>현재 수집 뉴스 기준</small>
        </article>
        <article className="rail-cell">
          <span>직접 종목</span>
          <strong>{directSymbolCount}</strong>
          <small>종목 태그가 붙은 뉴스</small>
        </article>
        <article className="rail-cell">
          <span>상위 흐름</span>
          <strong>{macroOnlyCount}</strong>
          <small>종목 없이 테마로 본 뉴스</small>
        </article>
        <article className="rail-cell">
          <span>가장 강한 영향</span>
          <strong>{strongestEvent ? formatNewsPercent(strongestEvent.impact_score) : "미측정"}</strong>
          <small>{strongestEvent ? koCode(strongestEvent.theme_key) : "데이터 없음"}</small>
        </article>
      </section>

      <section className="ledger-guide reveal delay-2" aria-labelledby="classification-guide-title">
        <div>
          <span>읽는 순서</span>
          <h2 id="classification-guide-title">태그 화면에서는 오류를 찾는다</h2>
        </div>
        <ol>
          <li>테마 그룹 이름이 뉴스 내용과 맞는지 본다.</li>
          <li>종목이 있으면 직접 종목 뉴스, 없으면 상위 흐름 뉴스로 본다.</li>
          <li>이상한 태그는 AI 결과 화면에서 한 번 더 비교한다.</li>
        </ol>
      </section>

      <section className="classification-grid reveal delay-2" aria-label="테마별 1차 분류">
        {groups.map((group) => (
          <article className="classification-card" key={group.themeKey}>
            <div className="trace-card-top">
              <div>
                <span className="metric-sub">뉴스 {group.events.length}개 · 종목 {group.symbols.size}개</span>
                <h2>{koCode(group.themeKey)}</h2>
                <p className="cluster-story-context">{group.themeName}</p>
              </div>
              <span className="relation-pill">{directionSummary(group)}</span>
            </div>
            <div className="tag-strip">
              {Array.from(group.symbols).slice(0, 8).map((symbol) => (
                <span key={`${group.themeKey}-${symbol}`}>{koCode(symbol)}</span>
              ))}
              {group.symbols.size === 0 ? <span>시장/테마 뉴스</span> : null}
            </div>
            <div className="news-row-list compact-news-row-list">
              {group.events.slice(0, 3).map((event) => (
                <NewsEventCard compact event={event} key={event.event_id} mode="classification" />
              ))}
            </div>
            <div className="btn-row">
              <Link className="btn btn-secondary" href={`/themes/${encodeURIComponent(group.themeKey)}` as Route}>
                테마 상세
              </Link>
              <Link className="btn btn-secondary" href="/ai-evidence">
                AI 분석과 비교
              </Link>
            </div>
          </article>
        ))}
      </section>
    </div>
  );
}
