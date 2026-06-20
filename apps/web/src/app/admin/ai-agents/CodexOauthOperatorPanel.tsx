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
    return "risk-low";
  }
  if (status === "device_auth_pending" || status === "device_code_expired" || status === "unknown") {
    return "risk-medium";
  }
  return "risk-high";
}

function shortStatus(status: CodexOauthOperatorStatus) {
  if (status.status === "healthy") {
    return "연결 정상";
  }
  if (status.status === "authenticated_smoke_required") {
    return "로그인 완료, smoke 필요";
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
        <span className="decision-brief-kicker">Codex OAuth 연결</span>
        <h2 className="decision-brief-title">코드 발급, 로그인 확인, smoke 검증을 순서대로 처리한다.</h2>
        <p className="decision-brief-copy">
          OpenAI API quota가 없을 때 쓰는 fallback 경로다. 버튼은 서버에서만 admin token을 붙여 실행하며,
          브라우저에는 token이나 OAuth 파일이 노출되지 않는다.
        </p>
        <div className="decision-brief-meta">
          <span>상태: {shortStatus(status)}</span>
          <span>마지막 확인: {formatDateTime(status.last_checked_at)}</span>
          <span>마지막 smoke: {status.last_smoke_status || "없음"}</span>
          <span>CLI 로그인: {status.login_probe_status || "not_checked"}</span>
          <span>주문 경계: {status.order_boundary}</span>
        </div>
      </div>
      <div className="decision-brief-grid">
        <div className={`decision-card ${statusTone(status.status)}`}>
          <span>현재 판정</span>
          <strong>{shortStatus(status)}</strong>
          <small>{status.summary}</small>
        </div>
        <div className="decision-card is-watch">
          <span>해야 할 일</span>
          <strong>{isPending ? "실행 중" : lastResult?.ok === false ? "실패" : "대기"}</strong>
          <small>{actionMessage(lastResult, status)}</small>
        </div>
        <div className="decision-card is-good">
          <span>거래 영향</span>
          <strong>없음</strong>
          <small>재로그인과 smoke는 AI 배치 확인용이다. 추천 weight, 주문, 포트폴리오를 바꾸지 않는다.</small>
        </div>
      </div>

      <div className="flow-steps">
        <div className="flow-step">
          <span>01</span>
          <strong>코드 발급</strong>
          <p>로그인이 필요하거나 코드가 만료됐을 때만 새 device code를 만든다.</p>
        </div>
        <div className="flow-step">
          <span>02</span>
          <strong>브라우저 인증</strong>
          <p>인증 URL을 열고 화면의 코드를 입력한다. 완료 후 이 화면으로 돌아온다.</p>
        </div>
        <div className="flow-step">
          <span>03</span>
          <strong>상태 확인</strong>
          <p>로그인 상태 새로고침으로 서버의 `codex login status` 결과를 확인한다.</p>
        </div>
        <div className="flow-step">
          <span>04</span>
          <strong>Smoke 검증</strong>
          <p>직접 smoke가 성공해야 실제 배치 AI fallback이 사용할 수 있다.</p>
        </div>
      </div>

      {status.auth_url || status.user_code ? (
        <div className="source-card">
          <span>브라우저에 입력할 코드</span>
          <strong>{status.user_code || "코드 미확인"}</strong>
          <p>
            만료 시각 {formatDateTime(status.expires_at)}. 링크를 열어 위 코드를 입력한 뒤 “로그인 상태 새로고침”을 누른다.
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
          1. 재로그인 코드 발급
        </button>
        <button
          className="btn btn-secondary"
          disabled={isPending}
          onClick={() => run(refreshCodexOauthStatusAction)}
          type="button"
        >
          2. 로그인 상태 새로고침
        </button>
        <button
          className="btn btn-secondary"
          disabled={isPending}
          onClick={() => run(runCodexOauthDirectSmokeAction)}
          type="button"
        >
          3. 직접 smoke 실행
        </button>
        <button
          className="btn btn-secondary"
          disabled={isPending}
          onClick={() => run(runCodexOauthNewsSmokeAction)}
          type="button"
        >
          4. 뉴스 번역·구조화 smoke
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
