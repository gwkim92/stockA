"use client";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import type { DecisionListItem } from "./DecisionList";
import styles from "./ReviewQueue.module.css";
export function ReviewQueue({ items }: { items: readonly DecisionListItem[] }) {
  const params = useSearchParams(), key = params.get("review");
  function setKey(value: string) {
    const next = new URLSearchParams(window.location.search); next.set("review", value);
    window.history.pushState(null, "", `/?${next}`);
  }
  const selected = items.find(item => item.key === key) ?? items[0];
  return <div className={styles.queue} data-testid="home-review-queue">
    <div className={styles.list}><div className={styles.columnLabels}><span>대상</span><span>확인할 변화·검토</span></div>
      {items.map(item => <button type="button" key={item.key} className={styles.row} aria-pressed={selected?.key === item.key} onClick={() => setKey(item.key)}><span><strong>{item.subject}</strong><small>{item.label}</small></span><span><strong>{item.title}</strong><small>{item.description}</small></span><span aria-hidden="true">↗</span></button>)}
      {!items.length && <p className={styles.empty}>수신된 보유 검토·사이클 전환 항목이 없습니다. 영역별 데이터 상태를 함께 확인하세요.</p>}
    </div>
    {selected && <aside className={styles.context} aria-label="선택한 검토 맥락"><span>{selected.label}</span><h3>{selected.subject} · {selected.title}</h3><p>{selected.description}</p><Link href={selected.href} prefetch={false}>{selected.actionLabel} →</Link><small>원래 검토·추천 기록을 읽습니다. 이 선택으로 판단을 승인하거나 변경하지 않습니다.</small></aside>}
  </div>;
}
