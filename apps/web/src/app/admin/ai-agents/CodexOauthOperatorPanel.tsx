"use client";

import { useState, useTransition } from "react";

import {
  refreshCodexOauthStatusAction,
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
  if (status === "healthy" || status === "authenticated_smoke_required") {
    return "is-ready";
  }
  if (status === "news_smoke_running" || status === "device_auth_pending" || status === "device_code_expired" || status === "unknown") {
    return "is-waiting";
  }
  return "is-blocked";
}

function shortStatus(status: CodexOauthOperatorStatus) {
  if (status.status === "healthy") {
    return "연결 정상";
  }
  if (status.status === "authenticated_smoke_required") {
    return "로그인 완료, smoke 필요";
  }
  if (status.status === "news_smoke_running") {
    return "뉴스 AI 확인 중";
  }
  if (status.status === "device_auth_pending") {
    return "코드 입력 대기";
  }
  if (status.status === "device_code_expired") {
    return "코드 만료";
  }
  if (status.status === "relogin_required") {
    return "재로그인 필요";
  }
  return status.label;
}

function isDeviceCodeExpired(status: CodexOauthOperatorStatus) {
  if (!status.expires_at) {
    return false;
  }
  const expiresAt = new Date(status.expires_at).getTime();
  return Number.isFinite(expiresAt) && expiresAt <= Date.now();
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

function primaryActionLabel(status: CodexOauthOperatorStatus) {
  if (status.status === "device_auth_pending" && !isDeviceCodeExpired(status) && status.auth_url) {
    return "인증 페이지 열기";
  }
  if (status.status === "authenticated_smoke_required") {
    return "AI 응답 확인";
  }
  if (status.status === "healthy") {
    return "뉴스 AI 확인";
  }
  if (status.status === "news_smoke_running") {
    return "뉴스 AI 실행 중";
  }
  return "새 로그인 코드 받기";
}

function primaryActionCopy(status: CodexOauthOperatorStatus) {
  if (status.status === "device_auth_pending" && !isDeviceCodeExpired(status)) {
    return "아래 코드를 OpenAI 인증 페이지에 입력한 뒤, 이 화면으로 돌아와 로그인 확인을 누른다.";
  }
  if (status.status === "authenticated_smoke_required") {
    return "로그인은 감지됐다. 이제 서버에서 실제 AI 응답을 받을 수 있는지 확인해야 한다.";
  }
  if (status.status === "healthy") {
    return "기본 연결은 정상이다. 뉴스 번역·구조화까지 실제 배치 경로로 확인할 수 있다.";
  }
  if (status.status === "news_smoke_running") {
    return "뉴스 번역·구조화 확인이 백그라운드에서 돌고 있다. 잠시 후 로그인 확인을 눌러 결과를 갱신한다.";
  }
  return "이전 로그인 토큰을 지우고 새 device code를 발급한다. 만료된 코드는 다시 쓰지 않는다.";
}

export default function CodexOauthOperatorPanel({ initialStatus }: Props) {
  const [status, setStatus] = useState(initialStatus);
  const [lastResult, setLastResult] = useState<CodexOauthActionState | null>(null);
  const [isPending, startTransition] = useTransition();
  const codeExpired = isDeviceCodeExpired(status);
  const effectiveStatus =
    status.status === "device_auth_pending" && codeExpired
      ? { ...status, status: "device_code_expired", label: "코드 만료", summary: "인증 코드가 만료됐다. 새 로그인 코드를 다시 받아야 한다." }
      : status;
  const canOpenAuth = effectiveStatus.status === "device_auth_pending" && Boolean(effectiveStatus.auth_url);
  const newsSmokeRunning = effectiveStatus.status === "news_smoke_running";

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
    <section className="codex-oauth-console" id="codex-oauth-operator" aria-label="Codex OAuth 연결 복구">
      <div className="codex-oauth-header">
        <div>
          <span className="codex-oauth-kicker">Codex OAuth</span>
          <h2>AI fallback 로그인 복구</h2>
          <p>
            OpenAI API 잔액이 없을 때 서버 배치가 사용하는 예비 AI 경로다. 이 화면에서는 로그인 복구와
            실제 응답 확인만 한다.
          </p>
        </div>
        <strong className={`codex-oauth-status ${statusTone(effectiveStatus.status)}`}>{shortStatus(effectiveStatus)}</strong>
      </div>

      <div className="codex-oauth-grid">
        <article className="codex-oauth-primary">
          <span>지금 할 일</span>
          <strong>{isPending ? "서버에서 처리 중" : lastResult?.ok === false ? "요청 실패" : primaryActionLabel(effectiveStatus)}</strong>
          <p>{isPending ? "버튼 실행 결과를 기다리고 있다." : actionMessage(lastResult, effectiveStatus) || primaryActionCopy(effectiveStatus)}</p>
          <small>추천 점수, 포트폴리오, 주문 제출에는 영향이 없다.</small>
        </article>

        <article className={`codex-oauth-code-card ${canOpenAuth ? "is-live" : "is-muted"}`}>
          <span>{codeExpired ? "만료된 코드" : "브라우저에 입력할 코드"}</span>
          <strong>{effectiveStatus.user_code || "코드 없음"}</strong>
          <p>
            {effectiveStatus.expires_at
              ? `만료 시각 ${formatDateTime(effectiveStatus.expires_at)}`
              : "새 로그인 코드가 아직 발급되지 않았다."}
          </p>
          {canOpenAuth ? (
            <a className="btn btn-primary" href={effectiveStatus.auth_url} target="_blank" rel="noreferrer">
              인증 페이지 열기
            </a>
          ) : null}
        </article>
      </div>

      <div className="codex-oauth-actions" aria-label="Codex OAuth 작업 버튼">
        <button
          className="btn btn-primary"
          disabled={isPending}
          onClick={() => run(startCodexOauthReloginAction)}
          type="button"
        >
          새 로그인 코드 받기
        </button>
        <button
          className="btn btn-secondary"
          disabled={isPending}
          onClick={() => run(refreshCodexOauthStatusAction)}
          type="button"
        >
          로그인 확인
        </button>
        <button
          className="btn btn-secondary"
          disabled={isPending}
          onClick={() => run(runCodexOauthDirectSmokeAction)}
          type="button"
        >
          AI 응답 확인
        </button>
        <button
          className="btn btn-secondary"
          disabled={isPending || newsSmokeRunning}
          onClick={() => run(runCodexOauthNewsSmokeAction)}
          type="button"
        >
          {newsSmokeRunning ? "뉴스 AI 실행 중" : "뉴스 AI 확인"}
        </button>
      </div>

      <div className="codex-oauth-steps" aria-label="복구 순서">
        {[
          ["01", "새 코드 받기", "서버의 낡은 토큰을 지우고 새 코드를 발급한다."],
          ["02", "OpenAI에 입력", "인증 페이지에서 위 코드를 입력한다."],
          ["03", "로그인 확인", "서버가 새 로그인 상태를 읽는지 확인한다."],
          ["04", "AI 응답 확인", "실제 배치 AI 호출이 되는지 검증한다."],
        ].map(([step, title, copy]) => (
          <article key={step}>
            <span>{step}</span>
            <strong>{title}</strong>
            <p>{copy}</p>
          </article>
        ))}
      </div>

      {effectiveStatus.last_error_summary ? (
        <div className="codex-oauth-alert">
          <strong>최근 실패</strong>
          <p>
            {effectiveStatus.last_error_code
              ? `${effectiveStatus.last_error_code}: ${effectiveStatus.last_error_summary}`
              : effectiveStatus.last_error_summary}
          </p>
        </div>
      ) : null}

      <details className="codex-oauth-details">
        <summary>운영 진단값 보기</summary>
        <dl>
          <div>
            <dt>마지막 확인</dt>
            <dd>{formatDateTime(effectiveStatus.last_checked_at)}</dd>
          </div>
          <div>
            <dt>AI 응답 확인</dt>
            <dd>{effectiveStatus.last_smoke_status || "기록 없음"}</dd>
          </div>
          <div>
            <dt>서버 로그인 감지</dt>
            <dd>{effectiveStatus.login_probe_status || "not_checked"}</dd>
          </div>
          <div>
            <dt>거래 경계</dt>
            <dd>{effectiveStatus.order_boundary}</dd>
          </div>
        </dl>
      </details>
    </section>
  );
}
