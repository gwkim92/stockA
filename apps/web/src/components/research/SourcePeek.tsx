"use client";
import Link from "next/link";
import type { Route } from "next";
import { useEffect, useId, useRef, useState } from "react";
import { shortDate, type SourceReaderData } from "@/lib/research-reader-model";
import styles from "./ResearchWorkspace.module.css";

export function SourcePeek({ documentId, label = "원천 발췌 읽기" }: { documentId: string; label?: string }) {
  const dialog = useRef<HTMLDialogElement>(null), trigger = useRef<HTMLButtonElement>(null);
  const heading = useId(), request = useRef<AbortController | null>(null);
  const [data, setData] = useState<SourceReaderData | null>(null);
  const [state, setState] = useState<"loading" | "ready" | "error">("loading");
  useEffect(() => () => request.current?.abort(), []);
  async function open() {
    request.current?.abort();
    const controller = new AbortController(); request.current = controller;
    setData(null); setState("loading"); if (!dialog.current?.open) dialog.current?.showModal();
    try {
      const response = await fetch(`/api/research-source/${encodeURIComponent(documentId)}`, { signal: controller.signal, cache: "no-store" });
      if (!response.ok) throw new Error("unavailable");
      const payload = await response.json() as { data: SourceReaderData };
      if (!controller.signal.aborted) { setData(payload.data); setState("ready"); }
    } catch { if (!controller.signal.aborted) setState("error"); }
  }
  return <>
    <button ref={trigger} type="button" className={styles.textButton} onClick={open}>{label} ↗</button>
    <dialog ref={dialog} className={styles.sourceDialog} aria-labelledby={heading} onClose={() => { request.current?.abort(); trigger.current?.focus(); }} onClick={event => { if (event.target === dialog.current) dialog.current.close(); }}>
      <div className={styles.sourceBody}>
        <header className={styles.sourceHeading}><div><span>원천 대조</span><h2 id={heading}>저장된 문서 발췌</h2></div><button autoFocus type="button" onClick={() => dialog.current?.close()} aria-label="원천 닫고 목록으로 돌아가기">닫기 ×</button></header>
        {state === "loading" && <p role="status">문서 발췌를 불러오는 중입니다.</p>}
        {state === "error" && <div role="status"><h3>원천을 불러오지 못했습니다</h3><p>문서가 없는 것으로 판단하지 않습니다. 목록의 선택과 검색은 유지됩니다.</p><button type="button" className={styles.textButton} onClick={open}>다시 시도</button></div>}
        {data && <><p className={styles.meta}>{data.publisher} · 공개일 {shortDate(data.filedAt, "미기록")} · 수집일 {shortDate(data.fetchedAt, "미기록")}</p><h3 className={styles.sourceTitle}>{data.koreanTitle ?? data.title}</h3>
          {data.integrityNotice && <p role="status" className={styles.note}><strong>{data.integrityNotice}</strong></p>}
          <p className={styles.note}>API가 제공한 발췌·요약입니다. 기사 전문 또는 검증이 끝난 투자 근거를 뜻하지 않습니다.</p>
          {data.excerpts?.map(excerpt => <section className={styles.excerpt} key={excerpt.id}><h4>{excerpt.section}</h4><small>{excerpt.locator}</small><p>{excerpt.summary}</p></section>)}
          {!data.excerpts?.length && <p className={styles.empty}>{data.excerpts === null ? "발췌 목록 미제공" : "저장된 발췌가 없습니다."}</p>}
          {data.koreanSummary && <section className={styles.excerpt}><h4>저장된 한국어 요약</h4><p>{data.koreanSummary}</p></section>}
          <p className={styles.meta}>{data.download === "restricted" ? "원문 다운로드 제한" : data.download === "unavailable" ? "원문 전달 경로 미제공" : "원문 접근 정책 미확인"}</p>
        </>}
        <Link href={`/source-documents/${encodeURIComponent(documentId)}` as Route} prefetch={false} className={styles.textButton}>문서 상세와 수집 기록 열기 →</Link>
      </div>
    </dialog>
  </>;
}
