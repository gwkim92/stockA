"use client";
import Link from "next/link";
import { WorkspaceIcon } from "@/components/shell/WorkspaceIcon";
import styles from "@/components/research/WorkspaceState.module.css";
/** Never render raw server exceptions, DSNs, provider text or credentials. */
export default function ErrorPage({ reset, unstable_retry }: { error: Error & { digest?: string }; reset?: () => void; unstable_retry?: () => void }) {
  const retry = () => { if (unstable_retry) unstable_retry(); else if (reset) reset(); else window.location.reload(); };
  return <section className={styles.state} aria-labelledby="workspace-error-title"><span className={styles.icon}><WorkspaceIcon name="health" /></span><h1 id="workspace-error-title">이 화면의 자료를 불러오지 못했습니다</h1><p>연결 상태나 응답을 확인해야 합니다. 다시 시도하거나 다른 리서치를 살펴보세요. 조회 실패를 데이터 없음으로 판단하지 마세요.</p><div className={styles.actions}><button type="button" onClick={retry}>다시 시도</button><Link href="/">리서치 홈으로</Link></div></section>;
}
