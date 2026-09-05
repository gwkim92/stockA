import type { Route } from "next";
import Link from "next/link";

import { DecisionList, type DecisionListItem } from "@/components/research/DecisionList";
import { WorkspaceIcon } from "@/components/shell/WorkspaceIcon";
import { StatusBadge } from "@/components/status/StatusBadge";
import { MetricStrip, type MetricItem } from "@/components/research/MetricStrip";

import { koCode, koReason } from "@/lib/korean-labels";
import { investorCopy } from "@/lib/presentation";
import { loadResearchHomeSnapshot } from "@/lib/research-home-data";
import {
  HOME_FEEDS, FEED_LABELS, changedCycles, count, feedCaption, fraction,
  homeHealth, recommendationStatus, record, rows, text, type HomeFeed,
} from "@/lib/research-home-model";

import styles from "./ResearchHome.module.css";

export const dynamic = "force-dynamic";

const countLabel = (value: unknown) => {
  const number = count(value);
  return number === null ? "미확인" : `${number.toLocaleString("ko-KR")}개`;
};
const ratioLabel = (value: unknown) => {
  const number = fraction(value);
  return number === null ? "미확인" : `${(number * 100).toFixed(1)}%`;
};
function SourceNote({ feed }: { feed: HomeFeed }) {
  return <p className={styles.sourceNote} role="status">{feedCaption(feed)}</p>;
}

export default async function HomePage() {
  const snapshot = await loadResearchHomeSnapshot();
  const { cycles, recommendations, news, portfolio } = snapshot.feeds;
  const dashboard = record(portfolio.data);
  const attention = record(dashboard.attention_summary);
  const transitions = changedCycles(cycles);
  const cycleRows = rows(cycles.data?.cycle_states);
  const recommendationRows = rows(recommendations.data?.recommendations);
  const newsRows = rows(news.data?.clusters);
  const loadedCount = HOME_FEEDS.filter((key) => snapshot.feeds[key].data !== null).length;
  const historicalCount = HOME_FEEDS.filter((key) => snapshot.feeds[key].dateState === "historical").length;

  const metrics: readonly MetricItem[] = [
    { label: "관측된 사이클 전환", value: cycles.data ? countLabel(transitions.length) : "미확인", context: "이전·현재 상태가 모두 있는 테마" },
    { label: "수신된 투자 후보", value: recommendations.data ? countLabel(recommendationRows.length) : "미확인", context: "원래 추천 순위 유지 · 주문 신호 아님" },
    { label: "보유 분석 커버리지", value: ratioLabel(record(dashboard.latest_metrics).weight_coverage_ratio), context: `${countLabel(attention.open_ticket_count)} 보완 항목` },
    { label: "리서치 데이터 연결", value: `${loadedCount} / ${HOME_FEEDS.length}`, context: historicalCount > 0 ? `${historicalCount}개 영역은 과거 기준` : "연결 성공과 근거 최신성은 별개" },
  ];

  // Surface state transitions, not an invented buy signal or a new score ranking.
  const selectedCycles = [...transitions, ...cycleRows.filter((row) => !transitions.includes(row))];
  const cycleItems: readonly DecisionListItem[] = selectedCycles
    .filter((row) => text(row.theme_key, ""))
    .slice(0, 4).map((row, index) => ({
      key: `${text(row.theme_key)}-${index}`,
      label: transitions.includes(row) ? "사이클 상태 전환" : "사이클 현황",
      subject: koCode(text(row.theme_key)),
      title: transitions.includes(row) ? `${koCode(text(row.previous_state))} → ${koCode(text(row.state))}` : koCode(text(row.state)),
      description: `연결 종목 ${countLabel(row.instrument_count)} · 모델 신뢰도 ${ratioLabel(row.confidence)}. 테마의 근거와 관련 종목을 함께 확인하세요.`,
      status: "watch",
      href: `/themes/${encodeURIComponent(text(row.theme_key))}` as Route,
      actionLabel: "테마 근거 보기",
    }));

  const recommendationItems: readonly DecisionListItem[] = recommendationRows
    .filter((row) => text(row.recommendation_id, ""))
    .slice(0, 5).map((row, index) => {
      const evidence = record(row.evidence_quality);
      const boundary = record(row.decision_boundary);
      const status = recommendationStatus(row, recommendations);
      return {
        key: `${text(row.recommendation_id)}-${index}`,
        label: `${count(row.rank_position) ?? "미확인"}위 · ${status === "source_limited" ? "원천 제한" : status === "ready" ? "페이퍼 검토 입력 허용" : "근거 확인 필요"}`,
        subject: text(row.symbol),
        title: text(evidence.title, `${text(row.name, text(row.symbol))} 투자 판단서`),
        description: `${text(evidence.summary, "투자 논리·촉매·반대 근거·무효화 조건을 상세에서 확인하세요.")} ${text(boundary.reason, "이 화면에서 주문이나 비중 변경은 실행하지 않습니다.")}`,
        status,
        href: `/recommendations/${encodeURIComponent(text(row.recommendation_id))}` as Route,
        actionLabel: "투자 판단서 읽기",
      };
    });

  const evidenceItems: readonly DecisionListItem[] = newsRows
    .filter((row) => text(row.evidence_id, ""))
    .slice(0, 4).map((row, index) => ({
      key: `${text(row.evidence_id)}-${index}`,
      label: text(row.theme_name, "시장 흐름"),
      subject: Array.isArray(row.symbols) ? row.symbols.filter((symbol) => typeof symbol === "string" && symbol && symbol !== "UNCLASSIFIED").slice(0, 3).join(" · ") || "시장 전반" : "연결 종목 미확인",
      title: text(row.story_label, text(row.title, "뉴스 근거 확인")),
      description: `관련 뉴스 ${countLabel(row.event_count)} · 모델 신뢰도 ${ratioLabel(row.confidence)}. 요약만으로 판단하지 말고 원문과 반대 근거를 확인하세요.`,
      status: "watch",
      href: `/ai-evidence/${encodeURIComponent(text(row.evidence_id))}` as Route,
      actionLabel: "원문·근거 읽기",
    }));

  const riskItems: readonly DecisionListItem[] = rows(dashboard.top_actions).slice(0, 5).map((row, index) => ({
    key: `review-${index}-${text(row.symbol)}`,
    label: `검토 우선순위 ${count(row.rank) ?? "미확인"}`,
    subject: text(row.symbol),
    title: investorCopy(koCode(text(row.action))),
    description: koReason(text(row.reason, "보유 논리와 검토 근거를 확인하세요.")),
    status: row.risk_level === "high" ? "blocked" : "watch",
    href: "/portfolio/coverage",
    actionLabel: "보유 논리 점검",
  }));

  return (
    <div className={styles.page} data-testid="research-home">
      <header className={styles.heading}>
        <div><p className={styles.eyebrow}>RESEARCH OVERVIEW</p><h1>리서치 브리핑</h1><p>시장 변화에서 기업의 근거까지, 오늘 살펴볼 흐름을 연결합니다.</p></div>
        <div className={styles.headingActions}><span className={styles.date}>{snapshot.requestedDate} <small>UTC</small></span><Link href="/recommendations">투자 후보 보기 <WorkspaceIcon name="arrow" /></Link></div>
      </header>
      <MetricStrip items={metrics} label="리서치 현황" />
      {loadedCount < HOME_FEEDS.length && <p className={styles.connectionNotice} role="status"><WorkspaceIcon name="health" />{homeHealth(snapshot)} · 연결된 영역은 계속 표시합니다.</p>}
      <div className={styles.workbench}>
        <div className={styles.primaryColumn}>
          <section className={styles.panel} aria-labelledby="home-cycle-title">
            <header className={styles.panelHeader}><div><span>01 / MARKET CYCLES</span><h2 id="home-cycle-title">지금 살펴볼 테마</h2></div><Link href="/cycle-map">사이클 지도 <WorkspaceIcon name="arrow" /></Link></header>
            <SourceNote feed={cycles} />
            {cycles.data && (cycleItems.length ? <div className={styles.cycleGrid}>{cycleItems.slice(0,3).map((item, index) => <article key={item.key} className={styles.cycleCard}>
              <div className={styles.cycleTop}><span className={styles.cycleIcon}><WorkspaceIcon name="cycle" /></span><span>{item.label}</span></div>
              <h3>{text(selectedCycles[index]?.theme_name, item.subject)}</h3>
              <p className={styles.cycleState}>{item.title}</p>
              <p>연결 종목 {countLabel(selectedCycles[index]?.instrument_count)}</p>
              <Link href={item.href}>테마 근거 보기 <WorkspaceIcon name="arrow" /></Link>
            </article>)}</div> : <p className={styles.empty}>조회된 사이클 목록이 비어 있습니다.</p>)}
            <p className={styles.panelFootnote}>상태 전환은 관측 결과이며 매수 신호가 아닙니다.</p>
          </section>
          <section className={styles.panel} aria-labelledby="home-candidates-title">
            <header className={styles.panelHeader}><div><span>02 / INVESTMENT RESEARCH</span><h2 id="home-candidates-title">검토할 투자 후보</h2></div><Link href="/recommendations">전체 후보 <WorkspaceIcon name="arrow" /></Link></header>
            <SourceNote feed={recommendations} />
            {recommendations.data && <DecisionList items={recommendationItems} emptyText="조회된 투자 후보 목록이 비어 있습니다." />}
            <p className={styles.panelFootnote}>원래 추천 순위를 유지합니다. 점수보다 논리·원천·무효화 조건을 확인하세요.</p>
          </section>
        </div>
        <aside className={styles.secondaryColumn} aria-label="함께 확인할 리서치">
          <section className={styles.panel} aria-labelledby="home-review-title">
            <header className={styles.panelHeader}><div><span>PORTFOLIO REVIEW</span><h2 id="home-review-title">보유 논리 재검토</h2></div><WorkspaceIcon name="portfolio" /></header>
            <SourceNote feed={portfolio} />
            {portfolio.data && (riskItems.length ? riskItems.map((item) => <article className={styles.sideItem} key={item.key}>
              <div className={styles.sideIdentity}><strong>{item.subject}</strong><StatusBadge kind={item.status} label="검토 필요" /></div><h3>{item.title}</h3><p>{item.description}</p><Link href={item.href}>{item.actionLabel} <WorkspaceIcon name="arrow" /></Link>
            </article>) : <p className={styles.empty}>조회된 우선 검토 항목이 없습니다. 전체 위험 평가는 포트폴리오 상세에서 확인하세요.</p>)}
          </section>
          <section className={styles.panel} aria-labelledby="home-news-title">
            <header className={styles.panelHeader}><div><span>CONNECTED EVIDENCE</span><h2 id="home-news-title">연결된 뉴스</h2></div><WorkspaceIcon name="news" /></header>
            <SourceNote feed={news} />
            {news.data && (evidenceItems.length ? evidenceItems.map((item) => <article className={styles.sideItem} key={item.key}>
              <span className={styles.newsTag}>{item.label}</span><h3>{item.title}</h3><p>{item.description}</p><div className={styles.newsBottom}><span>{item.subject}</span><Link href={item.href}>{item.actionLabel} <WorkspaceIcon name="arrow" /></Link></div>
            </article>) : <p className={styles.empty}>조회된 뉴스 근거 목록이 비어 있습니다.</p>)}
          </section>
          <Link href="/performance" className={styles.performanceCard}><WorkspaceIcon name="performance" /><span><strong>지난 판단은 어땠을까요?</strong><small>지난 판단의 수익률·벤치마크 대비 성과 확인</small></span><WorkspaceIcon name="arrow" /></Link>
        </aside>
      </div>
      <nav className={styles.journey} aria-label="투자 판단 경로">
        {[["/market-map","시장 읽기"],["/cycle-map","테마 탐색"],["/stocks","기업 분석"],["/recommendations","판단서 읽기"],["/portfolio/coverage","보유 재검토"]].map(([href,label],index) => <Link href={href as Route} key={href}><span>0{index+1}</span>{label}<WorkspaceIcon name="arrow" /></Link>)}
      </nav>
      <details className={styles.sourcePanel}><summary>영역별 데이터 상태 · {loadedCount}/{HOME_FEEDS.length} 연결</summary><p>분석 기준일과 원천 관측일은 다를 수 있습니다. 개별 원천은 상세 근거에서 확인하세요.</p><div className={styles.sourceGrid}>{HOME_FEEDS.map((key) => <div key={key}><strong>{FEED_LABELS[key]}</strong><span>{feedCaption(snapshot.feeds[key])}</span></div>)}</div></details>
      <section className={styles.systemNotice} aria-label="시스템 신뢰 상태"><p><strong>{homeHealth(snapshot)}</strong><span> · 실거래 주문과 자동 비중 변경은 실행하지 않습니다.</span></p><Link href="/data-health">데이터 상태 확인 <WorkspaceIcon name="arrow" /></Link></section>
    </div>
  );
}
