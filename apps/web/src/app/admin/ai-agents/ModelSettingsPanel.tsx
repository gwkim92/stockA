"use client";

import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import type { ModelSettings, ModelSelection } from "@/lib/model-settings-types";
import styles from "./ModelSettingsPanel.module.css";

const endpoint = "/api/ai-model-settings";
const date = (value: number | null) => value ? new Date(value * 1000).toLocaleString("ko-KR", { timeZone: "Asia/Seoul" }) : "미확인";
const modelLabel = (id: string | null) => ({ "gpt-5.6-terra": "Terra", "gpt-5.6-luna": "Luna", "gpt-5.6-sol": "Sol", "gpt-6-astra": "Astra" }[id || ""] || id || "미확인");

async function request(path = "", init?: RequestInit) {
  const response = await fetch(endpoint + path, { ...init, cache: "no-store", headers: { "Content-Type": "application/json" }, signal: AbortSignal.timeout(20000) });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error || "요청을 처리하지 못했습니다.");
  return payload;
}

export default function ModelSettingsPanel() {
  const [data, setData] = useState<ModelSettings | null>(null);
  const [draft, setDraft] = useState<ModelSelection | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const [code, setCode] = useState("");

  function accept(value: ModelSettings) {
    setData(value);
    setDraft({ revision: value.revision, default_model: value.default_model, overrides: value.overrides });
  }
  async function refresh() {
    setBusy(true); setError("");
    try { accept(await request()); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "설정을 불러오지 못했습니다."); }
    finally { setBusy(false); }
  }
  useEffect(() => { let active = true;
    request().then(value => { if (active) accept(value); }).catch(cause => { if (active) setError(cause.message); });
    return () => { active = false; };
  }, []);

  async function login(event: FormEvent) {
    event.preventDefault(); setBusy(true); setError(""); setNotice("");
    try { await request("/session", { method: "POST", body: JSON.stringify({ code: code.trim() }) }); setCode(""); accept(await request()); setNotice("관리자 잠금이 해제됐습니다. 모델을 선택하고 저장해 주세요."); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "잠금을 해제하지 못했습니다."); }
    finally { setBusy(false); }
  }
  async function logout() {
    setBusy(true); setError(""); setNotice("");
    try { await request("/session", { method: "DELETE" }); accept(await request()); setNotice("모델 설정을 잠갔습니다."); }
    catch (cause) { setError(cause instanceof Error ? cause.message : "잠그지 못했습니다."); }
    finally { setBusy(false); }
  }
  async function save(event: FormEvent) {
    event.preventDefault(); setBusy(true); setError(""); setNotice("");
    try { const saved = await request("", { method: "PATCH", body: JSON.stringify(draft) });
      setNotice(`설정 #${saved.revision} 저장 완료. 다음 Codex AI 호출부터 적용됩니다.`);
      accept(await request());
    } catch (cause) { setError(cause instanceof Error ? cause.message : "저장하지 못했습니다."); }
    finally { setBusy(false); }
  }
  const changes = data && draft ? [
    ...(data.default_model !== draft.default_model ? [`기본 모델: ${modelLabel(data.default_model)} → ${modelLabel(draft.default_model)}`] : []),
    ...data.workloads.filter(w => data.overrides[w.task] !== draft.overrides[w.task]).map(w => `${w.label}: ${modelLabel(data.overrides[w.task] || data.default_model)} → ${draft.overrides[w.task] ? modelLabel(draft.overrides[w.task]) : "기본 모델 사용"}`),
  ] : [];
  const canEdit = Boolean(data?.enabled && data.authorized && data.catalog.length && !busy);

  return <section className={styles.panel} aria-label="AI 모델 설정">
    <header className={styles.header}>
      <div><span className={styles.kicker}>실제 AI 사용처 · 모델 설정</span><h2>어떤 AI가 어디에서 일하는지</h2>
        <p>Codex 인증을 사용하는 5개 작업의 모델을 확인하고 변경합니다. 실행 중인 호출은 시작할 때의 설정을 유지합니다.</p></div>
      <button type="button" onClick={refresh} disabled={busy}>새로고침</button>
    </header>
    {error && <p role="alert" className={styles.error}>{error}</p>}
    {notice && <p role="status" className={styles.notice}>{notice}</p>}
    {!data || !draft ? <p role="status">{error ? "모델 설정을 확인할 수 없습니다. 새로고침으로 다시 시도해 주세요." : "서버 모델 설정을 불러오는 중…"}</p> : <>
      <div className={styles.summary}>
        <div><span>현재 기본 모델</span><strong>{modelLabel(data.default_model)}</strong><code>{data.default_model || "CLI 기본값 미확인"}</code></div>
        <div><span>변경 권한</span><strong>{data.authorized ? "관리자" : "조회 전용"}</strong><small>{data.authorized ? `세션 만료 ${date(data.session_expires_at)}` : "관리자 잠금 해제 후 변경 가능"}</small></div>
        <div><span>저장된 설정</span><strong>#{data.revision}</strong><small>작업별 예외 {Object.keys(data.overrides).length}개</small></div>
      </div>
      {!data.enabled ? <p className={styles.notice}>서버에 모델 설정 저장소가 아직 구성되지 않았습니다. 현재 실행 설정만 표시합니다.</p> :
        data.authorized ? <div className={styles.actions}><span>이 세션은 모델 설정만 변경할 수 있습니다.</span><button type="button" onClick={logout} disabled={busy}>설정 잠그기</button></div> :
        <details className={styles.unlock}><summary>관리자 잠금 해제</summary>
          <p>서버에서 발급한 일회용 접근 코드를 입력해 주세요. 코드는 10분 동안 유효하며, 이 브라우저의 변경 권한은 30일간 유지됩니다.</p>
          <form onSubmit={login} className={styles.actions}><label htmlFor="model-access-code">접근 코드</label><input id="model-access-code" type="password" autoComplete="off" value={code} onChange={event => setCode(event.target.value)} maxLength={64} required disabled={busy} /><button type="submit" disabled={busy || !code.trim()}>잠금 해제</button></form>
          <details><summary>서버에서 코드 발급하기</summary><p>운영 환경 파일을 적용한 서버 셸에서 실행합니다.</p><code>python -m stockanalysis.ai.model_settings grant-access</code></details>
        </details>}

      <form onSubmit={save}>
        <fieldset disabled={!canEdit} className={styles.fieldset}>
          <div className={styles.defaultChoice}><label htmlFor="default-ai-model">공통 기본 모델</label>
            <select id="default-ai-model" value={draft.default_model || ""} onChange={event => setDraft({ ...draft, default_model: event.target.value })}>
              {!data.catalog.some(m => m.id === draft.default_model) && <option value={draft.default_model || ""}>{draft.default_model || "모델 목록 미확인"}</option>}
              {data.catalog.map(model => <option value={model.id} key={model.id}>{model.label} · {model.id}</option>)}
            </select><p>‘기본 모델 사용’으로 둔 작업에 적용됩니다. 작업 실행 시 모델을 직접 지정하면 그 값이 우선합니다.</p></div>
          <div className={styles.workloads}>{data.workloads.map(workload => {
            const actual = workload.last_success;
            const pendingModel = draft.overrides[workload.task] || draft.default_model;
            return <article className={styles.workload} key={workload.task}>
              <div><h3>{workload.label}</h3><p>{workload.purpose}</p><small>{workload.execution}</small></div>
              <div className={styles.modelFacts}><div><span>저장된 적용 모델</span><strong>{workload.effective_model || "CLI 기본값 미확인"}</strong></div>
                <div><span>최근 성공 호출 · CLI 선택 모델</span><strong>{actual?.actual_model || "아직 확인된 실행 없음"}</strong><small>{actual ? `${date(actual.finished_at)} · 설정 #${actual.revision} · 추론 ${actual.reasoning_effort || "미확인"}` : "과거 codex-cli-default 기록은 실제 모델명으로 간주하지 않습니다."}</small></div>
              </div>
              <p className={styles.execution}>{workload.business_history ? `운영 DB 최근 호출 #${workload.business_history.invocation_id}: ${workload.business_history.provider} · 기록 모델 ${workload.business_history.model_name} · ${workload.business_history.status} · ${new Date(workload.business_history.created_at).toLocaleString("ko-KR", { timeZone: "Asia/Seoul" })}` : data.history_available ? "운영 DB에 이 작업의 호출 이력이 없습니다." : "운영 DB 호출 이력은 현재 조회되지 않았습니다."}</p>
              {workload.latest && <p className={styles.execution}>최근 시도: {({ running: "진행 중 또는 종료 기록 미수신", failed: "실패", succeeded: "성공" })[workload.latest.status]} · {modelLabel(workload.latest.selected_model)} · {date(workload.latest.started_at)}</p>}
              {workload.effective_model !== actual?.actual_model && <p className={styles.pending}>현재 설정 모델의 성공 실행 확인 대기</p>}
              <label htmlFor={`model-${workload.task}`}>작업별 모델</label>
              <select id={`model-${workload.task}`} value={draft.overrides[workload.task] || ""} onChange={event => {
                const overrides = { ...draft.overrides }; if (event.target.value) overrides[workload.task] = event.target.value; else delete overrides[workload.task]; setDraft({ ...draft, overrides });
              }}><option value="">기본 모델 사용 · {modelLabel(draft.default_model)}</option>
                {draft.overrides[workload.task] && !data.catalog.some(m => m.id === draft.overrides[workload.task]) && <option value={draft.overrides[workload.task]}>{draft.overrides[workload.task]} · 목록에서 제외됨</option>}
                {data.catalog.map(model => <option value={model.id} key={model.id}>{model.label} · {model.id}</option>)}
              </select><small>저장 후 적용: {pendingModel || "미확인"}</small>
              <details><summary>코드 위치</summary><code>src/stockanalysis/{workload.source}</code></details>
            </article>;
          })}</div>
        </fieldset>
        <div className={styles.saveBar}>
          <div><strong>{changes.length ? `${changes.length}개 설정 변경` : "저장할 변경 없음"}</strong>{changes.length > 0 && <ul>{changes.map(change => <li key={change}>{change}</li>)}</ul>}
            <small>저장은 AI 호출을 실행하지 않습니다. 다음 호출에서 선택된 모델을 확인할 수 있습니다.</small></div>
          <button type="submit" disabled={!canEdit || !changes.length}>{busy ? "처리 중…" : "모델 설정 저장"}</button>
        </div>
      </form>
      <p className={styles.footnote}>모델 목록: 인증된 서버 CLI에서 확인 · {date(data.catalog_checked_at)} KST. CLI 선택 모델은 CLI 시작 정보와 성공 반환을 기준으로 표시합니다. 제공자 내부 라우팅은 확인할 수 없습니다.</p>
      {!data.catalog.length && <p className={styles.pending}>선택 가능한 모델 목록이 없습니다. 서버 모델 목록을 갱신한 후 변경할 수 있습니다.</p>}
      <details className={styles.history}><summary>최근 변경 이력 {data.audit.length}건</summary>
        {data.audit.length ? <ol>{data.audit.map(entry => <li key={entry.revision}><strong>설정 #{entry.revision}</strong> · {date(entry.changed_at)}<p>기본 {modelLabel(entry.before.default_model)} → {modelLabel(entry.after.default_model)}</p>
          {data.workloads.filter(w => entry.before.overrides[w.task] !== entry.after.overrides[w.task]).map(w => <p key={w.task}>{w.label}: {entry.before.overrides[w.task] || "기본 모델"} → {entry.after.overrides[w.task] || "기본 모델"}</p>)}<small>변경자 {entry.actor}</small></li>)}</ol> : <p>아직 저장된 모델 변경이 없습니다.</p>}
      </details>
      <details className={styles.footnote}><summary>그 밖의 AI 관련 기능</summary>
        <p>뉴스 번역·이벤트 추출에는 OpenAI SDK 대체 경로도 있습니다. 이 화면은 현재 인증 경로인 Codex 모델을 설정하며, 제공자 전환이나 API 과금 설정은 변경하지 않습니다.</p>
        <p>OAuth 연결 점검은 진단용 호출이며 배치 분석과 별개입니다. 로컬 규칙·fixture·문서 청크 생성은 외부 모델을 호출하지 않습니다. 아래 에이전트 목록은 역할별 설계 정책이며, 모든 역할이 별도 AI를 호출한다는 뜻은 아닙니다.</p>
      </details>
    </>}
  </section>;
}
