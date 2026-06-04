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
  const aiLinkedCount = data.events.filter((event) => event.ai_evidence_id).length;
  const unreviewedCount = data.summary.unreviewed_event_count;
  const ruleCheckCount = Math.max(0, data.events.length - aiLinkedCount);
  const riskReviewCount = groups.reduce((count, group) => count + group.riskReview, 0);
  const classificationCommandCards = [
    {
      index: "01",
      label: "테마 묶음",
      title: groups.length > 0 ? `${groups.length.toLocaleString("ko-KR")}개 테마` : "테마 없음",
      metric: `뉴스 ${data.events.length.toLocaleString("ko-KR")}건 · 리스크 ${riskReviewCount.toLocaleString("ko-KR")}건`,
      body:
        groups.length > 0
          ? "뉴스가 어떤 상위 흐름으로 묶였는지 먼저 본다. 테마 이름이 뉴스 내용과 맞지 않으면 AI 근거와 대조한다."
          : "현재 필터 기준으로 묶을 테마가 없다. 수집 목록과 분류 배치 상태를 확인한다.",
      href: "#classification-groups",
      cta: "테마 묶음 보기",
      tone: groups.length > 0 ? "ready" : "block",
    },
    {
      index: "02",
      label: "직접 종목",
      title: directSymbolCount > 0 ? `${directSymbolCount.toLocaleString("ko-KR")}건` : "직접 종목 없음",
      metric: `종목 태그 ${directSymbolCount.toLocaleString("ko-KR")}건`,
      body:
        directSymbolCount > 0
          ? "명확한 회사명·티커 뉴스만 직접 종목으로 본다. 원문에 없는 티커가 붙었다면 AI 근거와 검증 결과에서 차단 여부를 본다."
          : "직접 종목 태그가 없다. 거시·테마 뉴스일 수 있으므로 억지로 종목을 붙이지 않는다.",
      href: "#classification-groups",
      cta: "종목 태그 확인",
      tone: directSymbolCount > 0 ? "watch" : "ready",
    },
    {
      index: "03",
      label: "상위 흐름",
      title: macroOnlyCount > 0 ? `${macroOnlyCount.toLocaleString("ko-KR")}건` : "상위 흐름 없음",
      metric: `시장/테마 뉴스 ${macroOnlyCount.toLocaleString("ko-KR")}건`,
      body:
        macroOnlyCount > 0
          ? "금리, 물가, 정책, 에너지 같은 뉴스는 개별 종목보다 상위 흐름으로 먼저 저장하고 이후 종목 민감도에 따라 전파한다."
          : "현재 목록에서는 종목 없는 상위 흐름 뉴스가 두드러지지 않는다.",
      href: "/cycle-map",
      cta: "사이클 지도 보기",
      tone: macroOnlyCount > 0 ? "watch" : "ready",
    },
    {
      index: "04",
      label: "AI 근거 비교",
      title: aiLinkedCount > 0 ? `${aiLinkedCount.toLocaleString("ko-KR")}건 연결` : "AI 비교 전",
      metric: `규칙만 ${ruleCheckCount.toLocaleString("ko-KR")}건 · AI 미연결 ${unreviewedCount.toLocaleString("ko-KR")}건`,
      body:
        aiLinkedCount > 0
          ? "1차 태그와 AI 구조화 결과가 같은 방향인지 본다. 불일치하거나 낮은 신뢰도는 추천 근거로 쓰지 않는다."
          : "이 화면의 태그는 아직 최종 판단이 아니다. AI 근거와 검증 결과가 붙을 때까지 추천 입력으로 보류한다.",
      href: "/ai-evidence",
      cta: "AI 근거와 비교",
      tone: aiLinkedCount > 0 ? "ready" : "watch",
    },
  ];

  return (
    <div className="pageStack classification-page decision-page">
      <section className="decision-brief reveal" aria-labelledby="classification-title">
        <div className="decision-brief-main">
          <span className="decision-brief-kicker">1차 분류 태그 · {data.as_of_date}</span>
          <h1 className="decision-brief-title" id="classification-title">
            1차 태그 {groups.length.toLocaleString("ko-KR")}개, AI 연결 {aiLinkedCount.toLocaleString("ko-KR")}건
          </h1>
          <p className="decision-brief-copy">
            이 화면은 최종 투자 판단이 아니라 규칙 기반 첫 해석이다. 테마가 맞는지, 종목을 억지로 붙였는지 보고 AI 구조화·검증 결과와 비교한다.
          </p>
          <div className="decision-brief-meta" aria-label="1차 분류 핵심 상태">
            <span>직접 종목 {directSymbolCount.toLocaleString("ko-KR")}건</span>
            <span>상위 흐름 {macroOnlyCount.toLocaleString("ko-KR")}건</span>
            <span>규칙만 {ruleCheckCount.toLocaleString("ko-KR")}건</span>
            <span>AI 미연결 {unreviewedCount.toLocaleString("ko-KR")}건</span>
          </div>
        </div>
        <div className="decision-brief-grid">
          {classificationCommandCards.map((card) => (
            <a
              className={`decision-card ${
                card.tone === "ready" ? "is-good" : card.tone === "watch" ? "is-watch" : "is-block"
              }`}
              href={card.href}
              key={card.index}
            >
              <span>{card.label}</span>
              <strong>{card.title}</strong>
              <small>{card.metric} · {card.body}</small>
              <b>{card.cta}</b>
            </a>
          ))}
        </div>
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
          <small>태그와 방향 확인</small>
        </Link>
        <Link className="screen-switch-card" href="/ai-evidence">
          <span>03</span>
          <strong>AI 근거 목록</strong>
          <small>AI 근거 후보 확인</small>
        </Link>
        <Link className="screen-switch-card" href={"/ai-evidence/results" as Route}>
          <span>04</span>
          <strong>구조화 결과</strong>
          <small>통과 결과 확인</small>
        </Link>
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

      <section className="classification-grid reveal delay-2" id="classification-groups" aria-label="테마별 1차 분류">
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
                AI 근거와 비교
              </Link>
            </div>
          </article>
        ))}
      </section>
    </div>
  );
}
