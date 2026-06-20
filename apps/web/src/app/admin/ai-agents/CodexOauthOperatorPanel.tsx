"use client";

import { useState, useTransition } from "react";

import {
  runCodexOauthDirectSmokeAction,
  runCodexOauthNewsSmokeAction,
  startCodexOauthReloginAction,
  type CodexOauthActionState,
} from "./actions";
import type { CodexOauthOperatorStatus } from "@/lib/types";

type Props = {
  initialStatus: CodexOauthOperatorStatus;
};

function statusTone(status: string) {
  if (status === "healthy") {
    return "risk-low";
  }
  if (status === "device_auth_pending" || status === "device_code_expired" || status === "unknown") {
    return "risk-medium";
  }
  return "risk-high";
}

function formatDateTime(value: string) {
  if (!value) {
    return "기록 없음";
  }
  return value.replace("T", " ").replace("Z", " UTC");
}

function actionMessage(result: CodexOauthActionState | null, status: CodexOauthOperatorStatus) {
  if (result) {
    return result.message;
  }
  return status.next_action || status.summary;
}

export default function CodexOauthOperatorPanel({ initialStatus }: Props) {
  const [status, setStatus] = useState(initialStatus);
  const [lastResult, setLastResult] = useState<CodexOauthActionState | null>(null);
  const [isPending, startTransition] = useTransition();

  function run(action: () => Promise<CodexOauthActionState>) {
    startTransition(async () => {
      const result = await action();
      setLastResult(result);
      if (result.status) {
        setStatus(result.status);
      }
    });
  }

  return (
    <section className="decision-brief" id="codex-oauth-operator" aria-label="codex oauth operator">
      <div className="decision-brief-main">
        <span className="decision-brief-kicker">Codex OAuth 재로그인</span>
        <h2 className="decision-brief-title">OpenAI quota가 없을 때 쓰는 무료 fallback 로그인 상태를 관리한다.</h2>
        <p className="decision-brief-copy">
          이 영역은 운영자 action이다. 버튼은 서버에서만 admin token을 붙여 실행하며, 브라우저에는 토큰이나 OAuth
          파일이 노출되지 않는다.
        </p>
        <div className="decision-brief-meta">
          <span>상태: {status.label}</span>
          <span>마지막 확인: {formatDateTime(status.last_checked_at)}</span>
          <span>마지막 smoke: {status.last_smoke_status || "없음"}</span>
          <span>주문 경계: {status.order_boundary}</span>
        </div>
      </div>
      <div className="decision-brief-grid">
        <div className={`decision-card ${statusTone(status.status)}`}>
          <span>Codex OAuth 상태</span>
          <strong>{status.label}</strong>
          <small>{status.summary}</small>
        </div>
        <div className="decision-card is-watch">
          <span>다음 행동</span>
          <strong>{isPending ? "실행 중" : lastResult?.ok === false ? "실패" : "대기"}</strong>
          <small>{actionMessage(lastResult, status)}</small>
        </div>
        <div className="decision-card is-good">
          <span>거래 영향</span>
          <strong>없음</strong>
          <small>재로그인과 smoke는 AI 배치 확인용이다. 추천 weight, 주문, 포트폴리오를 바꾸지 않는다.</small>
        </div>
      </div>

      {status.auth_url || status.user_code ? (
        <div className="source-card">
          <span>Device Auth</span>
          <strong>{status.user_code || "코드 미확인"}</strong>
          <p>
            만료 시각 {formatDateTime(status.expires_at)}. 링크를 열어 위 코드를 입력한 뒤 smoke를 실행한다.
          </p>
          {status.auth_url ? (
            <a className="text-link" href={status.auth_url} target="_blank" rel="noreferrer">
              인증 URL 열기
            </a>
          ) : null}
        </div>
      ) : null}

      <div className="route-grid compact-routes">
        <button
          className="btn btn-primary"
          disabled={isPending}
          onClick={() => run(startCodexOauthReloginAction)}
          type="button"
        >
          재로그인 시작
        </button>
        <button
          className="btn btn-secondary"
          disabled={isPending}
          onClick={() => run(runCodexOauthDirectSmokeAction)}
          type="button"
        >
          재로그인 후 직접 smoke
        </button>
        <button
          className="btn btn-secondary"
          disabled={isPending}
          onClick={() => run(runCodexOauthNewsSmokeAction)}
          type="button"
        >
          뉴스 번역·구조화 smoke
        </button>
      </div>

      {status.last_error_summary ? (
        <div className="empty-state">
          <strong>최근 오류</strong>
          <p>{status.last_error_code ? `${status.last_error_code}: ${status.last_error_summary}` : status.last_error_summary}</p>
        </div>
      ) : null}
    </section>
  );
}
