import Link from "next/link";

import type { CodexOauthStatusView } from "./codex-oauth-status-view";
import styles from "./CodexOauthOperatorPanel.module.css";

type Props = {
  readonly status: CodexOauthStatusView;
};

export default function CodexOauthOperatorPanel({ status }: Props) {
  return (
    <section
      className={styles.panel}
      id="codex-oauth-operator"
      aria-labelledby="codex-oauth-status-title"
    >
      <div className={styles.header}>
        <div>
          <span className={styles.kicker}>Codex OAuth · 상태 조회 전용</span>
          <h2 id="codex-oauth-status-title">예비 AI 연결 상태</h2>
          <p>
            이 화면은 저장된 운영 상태만 읽습니다. 재로그인, 실제 AI 호출 점검, 인증 정보 처리는 서버 운영 경계에서만
            실행합니다.
          </p>
        </div>
        <strong className={`${styles.status} ${styles[status.tone]}`}>{status.statusLabel}</strong>
      </div>

      <div className={styles.summaryGrid}>
        <article className={styles.summaryCard}>
          <span>현재 연결 판단</span>
          <strong>{status.statusLabel}</strong>
          <p>{status.statusSummary}</p>
        </article>
        <article className={styles.channelCard}>
          <span>운영 실행 채널</span>
          <strong>{status.operationChannel}</strong>
          <p>
            웹 요청은 관리자 토큰을 쓰지{"\u00a0"}않습니다. 인증 코드와 URL도 화면에 내보내지{"\u00a0"}않습니다.
          </p>
        </article>
      </div>

      <dl className={styles.boundaryGrid}>
        <div>
          <dt>접근 경계</dt>
          <dd>{status.accessBoundary}</dd>
        </div>
        <div>
          <dt>마지막 상태 확인</dt>
          <dd>
            {status.lastCheckedIso ? <time dateTime={status.lastCheckedIso}>{status.lastCheckedLabel}</time> : status.lastCheckedLabel}
          </dd>
        </div>
        <div>
          <dt>실제 AI 호출 점검</dt>
          <dd>{status.lastSmokeLabel}</dd>
        </div>
        <div>
          <dt>서버 로그인 감지</dt>
          <dd>{status.loginProbeLabel}</dd>
        </div>
        <div className={status.executionTone === "blocked" ? styles.blockedBoundary : undefined}>
          <dt>거래 경계</dt>
          <dd>{status.executionBoundary}</dd>
        </div>
      </dl>

      <div className={styles.nextAction}>
        <div>
          <span>다음 조치</span>
          <strong>{status.nextAction}</strong>
        </div>
        <Link href="/data-health">데이터·AI 상태 보기</Link>
      </div>
    </section>
  );
}
