import Link from "next/link";
import type { ReactNode } from "react";
import type { ReviewResult } from "@/lib/review-workspace-data";
import { dateContext, words } from "@/lib/review-workspace-model";
import styles from "./ReviewWorkspace.module.css";
import compactStyles from "./ReviewCompactMetrics.module.css";

export function ReviewFrame({ kind, result, children }: {
  kind: "portfolio" | "performance";
  result: ReviewResult;
  children: ReactNode;
}) {
  const portfolio = kind === "portfolio";
  const report = result.report;
  const errors = {
    date: "조회 기준일을 확인해 주세요",
    timeout: "자료 응답이 지연되고 있습니다",
    invalid: "자료의 계정 또는 형식을 확인해야 합니다",
    http: "이 화면의 자료를 불러오지 못했습니다",
    network: "이 화면의 자료를 불러오지 못했습니다",
  };
  return (
    <div className={styles.page} data-testid="review-workspace">
      <header className={styles.header}>
        <div>
          <span>{portfolio ? "HOLDINGS REVIEW" : "DECISION OUTCOMES"}</span>
          <h1>{portfolio ? "보유 검토" : "판단 성과"}</h1>
        </div>
        <form method="get" className={styles.dateForm} aria-label="보고서 기준일 선택">
          <label>
            {portfolio ? "보유 기준일" : "성과 종료 기준일"}
            <input type="date" name="date" max={result.today} defaultValue={result.requestedDate} required />
          </label>
          <button type="submit">조회</button>
        </form>
      </header>
      <nav className={styles.tabs} aria-label="보유와 성과">
        <Link href={`/portfolio/coverage?date=${result.requestedDate}`} aria-current={portfolio ? "page" : undefined}>보유 검토</Link>
        <Link href={`/performance?date=${result.requestedDate}`} aria-current={!portfolio ? "page" : undefined}>판단 성과</Link>
      </nav>
      <p className={styles.context}>
        {words(report?.raw.portfolio_name, "Long Term Paper")} · 페이퍼 포트폴리오 · 실거래 주문 비활성
        {report && <><br />{dateContext(portfolio ? report.raw.as_of_date : report.raw.measurement_end_date, result.requestedDate)}{report.partial ? " · 일부 결과" : ""}</>}
      </p>
      {report ? children : (
        <section className={styles.empty} role="status">
          <h2>{errors[result.issue ?? "network"]}</h2>
          <p>{result.issue === "date" ? "유효한 날짜 한 개를 입력하세요. 미래 날짜는 조회하지 않습니다." : "불러오지 못한 자료를 빈 포트폴리오나 수익률 0으로 표시하지 않습니다."}</p>
          <Link href={portfolio ? "/portfolio/coverage" : "/performance"}>최신 기준 다시 조회</Link>
        </section>
      )}
      {portfolio && <p className={styles.note}><Link href="/portfolio/coverage/details" prefetch={false}>위험예산·분석 상세 ↗</Link></p>}
    </div>
  );
}

export function ReviewMetrics({ items, note, compact = false }: {
  items: readonly { label: string; value: string; detail: string; hint?: string }[];
  note: string;
  compact?: boolean;
}) {
  return (
    <section className={styles.metricBlock} aria-label="보고서 요약">
      <dl className={`${styles.metrics} ${compact ? compactStyles.strip : ""}`} data-compact={compact}>
        {items.map(item => (
          <div key={item.label}>
            <dt>{item.label}</dt>
            <dd>{item.value}{item.hint && <small style={{ display: "block", fontWeight: 400, marginTop: 4 }}>{item.hint}</small>}</dd>
          </div>
        ))}
      </dl>
      <details className={styles.summaryNotes}>
        <summary>집계 범위·해석 안내</summary>
        <p>{note}</p>
        <dl className={styles.factList}>{items.map(item => (
          <div key={item.label}><dt>{item.label}</dt><dd>{item.detail}</dd></div>
        ))}</dl>
      </details>
    </section>
  );
}
