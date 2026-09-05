import type { Route } from "next";
import Link from "next/link";

import { DecisionList, type DecisionListItem } from "@/components/research/DecisionList";
import { DecisionSummary } from "@/components/research/DecisionSummary";
import { MetricStrip, type MetricItem } from "@/components/research/MetricStrip";
import { ResearchSection } from "@/components/research/ResearchSection";
import { koCode, koReason } from "@/lib/korean-labels";
import { investorCopy } from "@/lib/presentation";
import { loadResearchHomeSnapshot } from "@/lib/research-home-data";
import {
  HOME_FEEDS, FEED_LABELS, changedCycles, count, feedCaption, fraction,
  homeHealth, recommendationStatus, record, rows, text, type HomeFeed,
} from "@/lib/research-home-model";

import styles from "./HomePage.module.css";
import research from "./ResearchHome.module.css";

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
  return <p className={research.sourceNote} role="status">{feedCaption(feed)}</p>;
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
      <div className={research.intro}><DecisionSummary
        eyebrow={`중장기 투자 리서치 · 조회 기준 ${snapshot.requestedDate} UTC`}
        title="시장 변화에서 투자 판단까지"
        description="어떤 테마가 바뀌었는지, 어떤 기업의 투자 논리가 유효한지, 보유 판단을 다시 볼 이유가 있는지 확인하세요. 3개월부터 1년 이상을 보는 리서치 화면입니다."
        primaryAction={{ href: "/cycle-map", label: "사이클 지도 보기" }}
        secondaryActions={[
          { href: "/recommendations", label: "투자 후보 검토" },
          { href: "/portfolio/coverage", label: "보유 논리 점검" },
        ]}
        side={<><strong>{loadedCount === 0 ? "분석 데이터 연결을 확인해 주세요" : "논리·촉매·무효화 조건"}</strong><p>후보를 검토한 뒤 보유 논리가 유지되는지 계속 점검합니다. 실거래 주문은 비활성입니다.</p></>}
      /></div>
      <div className={research.metrics}><MetricStrip items={metrics} label="리서치 현황" /></div>
      <nav className={styles.decisionLine} aria-label="투자 판단 경로">
        {[
          ["/market-map", "시장", "거시 배경"], ["/cycle-map", "사이클", "테마 변화"],
          ["/intelligence", "뉴스", "원문 근거"], ["/stocks", "종목", "기업 분석"],
          ["/recommendations", "투자 후보", "논리·무효화 조건"], ["/portfolio/coverage", "포트폴리오", "보유 재검토"],
        ].map(([href, label, context]) => <Link href={href as Route} key={href}><span>{label}</span><small>{context}</small></Link>)}
      </nav>
      <ResearchSection eyebrow="시장 → 테마" title="어떤 사이클이 바뀌었나" description="관측된 상태 전환을 먼저 봅니다. 전환 방향만으로 상승 가능성이나 매수 적합성을 단정하지 않습니다.">
        <SourceNote feed={cycles} />
        {cycles.data && <DecisionList items={cycleItems} emptyText="조회된 사이클 목록이 비어 있습니다." />}
      </ResearchSection>
      <ResearchSection eyebrow="테마 → 기업 → 투자 논리" title="검토할 투자 후보와 판단 근거" description="기존 추천 순위를 유지합니다. 원천 제한, 투자 논리와 무효화 조건을 읽은 뒤 판단하세요.">
        <SourceNote feed={recommendations} />
        {recommendations.data && <DecisionList items={recommendationItems} emptyText="조회된 투자 후보 목록이 비어 있습니다." />}
      </ResearchSection>
      <ResearchSection eyebrow="판단을 뒷받침하는 자료" title="연결된 뉴스와 원문 근거" description="관련 기업과 원문을 함께 읽고, 현재 투자 논리를 강화하는지 약화하는지 비교하세요.">
        <SourceNote feed={news} />
        {news.data && <DecisionList items={evidenceItems} emptyText="조회된 뉴스 근거 목록이 비어 있습니다." />}
      </ResearchSection>
      <ResearchSection eyebrow="추천 이후의 검토" title="기존 보유 논리를 다시 볼 항목" description="보유 비중, 투자 논리, 성과 측정의 공백을 확인하세요. 표시할 항목이 없다는 것이 위험이 없다는 뜻은 아닙니다.">
        <SourceNote feed={portfolio} />
        {portfolio.data && <DecisionList items={riskItems} emptyText="조회된 우선 검토 항목이 없습니다. 전체 위험 평가는 포트폴리오 상세에서 확인하세요." />}
      </ResearchSection>
      <p className={research.performanceLink}><Link href="/performance">지난 판단의 수익률·벤치마크 대비 성과 확인</Link></p>
      <details className={research.sourcePanel}>
        <summary>영역별 데이터 상태 · {loadedCount}/{HOME_FEEDS.length} 연결</summary>
        <p>API가 제공한 분석 기준일입니다. 개별 원천의 관측일과 최신성은 상세 근거에서 확인하세요.</p>
        <div className={research.sourceGrid}>{HOME_FEEDS.map((key) => <div key={key}>
          <strong>{FEED_LABELS[key]}</strong><span>{feedCaption(snapshot.feeds[key])}</span>
        </div>)}</div>
      </details>
      <section className={styles.systemNotice} aria-label="시스템 신뢰 상태">
        <div><span>리서치와 운영 상태 구분</span><strong>{homeHealth(snapshot)}</strong><p>수집 실패의 영향 범위, 원천 기준일, 성과 측정 대기 항목을 확인하세요.</p></div>
        <Link href="/data-health">데이터 상태 확인</Link>
      </section>
    </div>
  );
}
