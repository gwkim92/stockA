import Link from "next/link";
import type { Route } from "next";
import type { ReactNode } from "react";
import type { ReaderIssue } from "@/lib/research-reader-data";
import styles from "./ResearchReader.module.css";
export function ReaderFrame({ title, eyebrow, subtitle, chapters, children, aside }: {
  title: string; eyebrow: string; subtitle?: string; chapters: readonly (readonly [string, string])[]; children: ReactNode; aside: ReactNode;
}) {
  return <div className={styles.page} data-testid="research-reader">
    <header className={styles.header}><span>{eyebrow}</span><h1>{title}</h1>{subtitle && <p>{subtitle}</p>}</header>
    <nav className={styles.chapters} aria-label="문서 목차">{chapters.map(([id, label]) => <a href={`#${id}`} key={id}>{label}</a>)}</nav>
    <div className={styles.layout}><div className={styles.reading}>{children}</div><aside className={styles.sidebar} aria-label="문서 맥락">{aside}</aside></div>
  </div>;
}
export function ReaderSection({ id, title, kicker, children }: { id: string; title: string; kicker?: string; children: ReactNode }) {
  return <section className={styles.section} id={id} aria-labelledby={`${id}-title`}><header>{kicker && <span>{kicker}</span>}<h2 id={`${id}-title`}>{title}</h2></header>{children}</section>;
}
export function ReaderLink({ href, children }: { href: string | null; children: ReactNode }) {
  return href ? <Link className={styles.link} prefetch={false} href={href as Route}>{children}</Link> : null;
}
export function ReaderUnavailable({ issue }: { issue: ReaderIssue | null }) {
  return <section className={styles.unavailable} role="status"><h1>{issue === "timeout" ? "자료 응답이 지연되고 있습니다" : issue === "invalid" ? "요청한 자료와 응답을 대조해야 합니다" : "자료를 불러오지 못했습니다"}</h1><p>조회 실패를 빈 문서나 검토 완료로 표시하지 않습니다.</p><a className={styles.link} href="">다시 조회</a><ReaderLink href="/">리서치 홈으로</ReaderLink></section>;
}
export function ReaderFacts({ items }: { items: readonly (readonly [string, string])[] }) {
  return <dl className={styles.facts}>{items.map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}</dl>;
}
export function StoredList({ items, missing }: { items: string[] | null; missing: string }) {
  return items === null ? <p className={styles.empty}>{missing}</p> : !items.length ? <p className={styles.empty}>기록된 항목이 없습니다.</p> : <ul className={styles.claims}>{items.map((item, i) => <li key={i}>{item}</li>)}</ul>;
}
