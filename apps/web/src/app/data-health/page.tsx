import { getDataHealth } from "@/lib/frontend-api";
import { koCode } from "@/lib/korean-labels";
import type { DataHealthData } from "@/lib/types";

export const dynamic = "force-dynamic";
export const metadata = { title: "데이터 수집" };

type PipelineRun = DataHealthData["pipeline_runs"][number];
type SchedulerActivation = DataHealthData["scheduler"]["activation"];
type SchedulerStatus = DataHealthData["scheduler"];
type ManualIngestSmoke = DataHealthData["manual_local_ingest_smoke"];
type LocalIngestWorker = DataHealthData["local_ingest_worker"];

function statusRiskClass(value: string) {
  if (value === "healthy" || value === "succeeded" || value === "configured") {
    return "risk-low";
  }
  if (value === "attention_required" || value === "stale") {
    return "risk-medium";
  }
  return "risk-high";
}

function findPipelineRun(data: DataHealthData, jobId: string, pipelineName: string) {
  return (
    data.pipeline_runs.find((run) => run.job_id === jobId)
    ?? data.pipeline_runs.find((run) => run.pipeline_name === pipelineName)
    ?? null
  );
}

function runStateLabel(run: PipelineRun | null) {
  if (!run) {
    return "실행 이력 없음";
  }
  if (run.latest_status === "succeeded" && run.health_status === "ok") {
    return "최근 실행 성공";
  }
  if (run.latest_status === "succeeded") {
    return `성공 · ${koCode(run.health_status)}`;
  }
  return `${koCode(run.latest_status)} · ${koCode(run.health_status)}`;
}

function automationStateLabel(schedulerActivation: SchedulerActivation) {
  if (schedulerActivation.activation_allowed) {
    return "반복 실행 설정됨";
  }
  if (schedulerActivation.status === "pending_manual_approval") {
    return "로컬 반복 실행 미설정";
  }
  return koCode(schedulerActivation.status);
}

function cadenceLabel(run: PipelineRun | null, fallback: string) {
  if (!run) {
    return fallback;
  }
  return `${koCode(run.cadence)} · ${run.expected_after_local}`;
}

function finishedAtLabel(run: PipelineRun | null) {
  return run?.finished_at ?? "아직 완료 기록 없음";
}

function schedulerReadinessTitle(scheduler: SchedulerStatus) {
  const activation = scheduler.activation;
  if (activation.activation_allowed && activation.scheduler_activation !== "not_installed") {
    return "반복 실행기 연결 가능";
  }
  if (activation.status === "pending_manual_approval") {
    return "반복 실행기는 아직 연결되지 않음";
  }
  if (scheduler.install_status === "not_installed") {
    return "반복 실행기는 아직 연결되지 않음";
  }
  return koCode(activation.status);
}

function schedulerReadinessExplanation(scheduler: SchedulerStatus) {
  const activation = scheduler.activation;
  if (activation.activation_allowed && activation.scheduler_activation !== "not_installed") {
    return "승인 관문과 실행기 상태가 반복 실행을 허용하는 상태다. 외부 배포가 아니라도 로컬 반복 실행기로 운영할 수 있다.";
  }
  if (activation.status === "pending_manual_approval") {
    return "최근 파이프라인 실행은 성공했지만, 자동 반복 실행기는 아직 연결되지 않았다. 현재 목표는 외부 서버 배포가 아니라 로컬에서 수동 실행과 상태 확인을 먼저 안정화하는 것이다.";
  }
  if (activation.status === "not_configured") {
    return "반복 실행 report가 연결되지 않아 로컬 자동 실행 여부를 판단할 수 없다.";
  }
  if (activation.status === "invalid_report") {
    return "반복 실행 report 형식이 맞지 않아 운영 근거로 사용할 수 없다.";
  }
  return "현재 반복 실행 상태는 화면의 승인 관문과 다음 단계 값을 기준으로 다시 확인해야 한다.";
}

function schedulerNextStepLabel(activation: SchedulerActivation) {
  if (activation.manual_next_step === "data-operations-live-scheduler-activation-request") {
    return "외부 서버 배포는 보류하고, 로컬 실행 순서와 수동 ingest smoke를 먼저 확정한다.";
  }
  if (activation.manual_next_step === "configure_scheduler_activation_gate_report") {
    return "repo 밖 반복 실행 gate report 경로를 설정한다.";
  }
  if (activation.manual_next_step === "regenerate_scheduler_activation_gate_report") {
    return "깨진 scheduler report를 다시 생성한다.";
  }
  return koCode(activation.manual_next_step);
}

function schedulerInstallLabel(value: string) {
  if (value === "not_installed") {
    return "반복 실행기 미설정";
  }
  return koCode(value);
}

function schedulerApprovalGateLabel(value: string) {
  if (value === "blocked_pending_manual_approval" || value === "pending_manual_approval") {
    return "로컬 반복 실행 전 관문 닫힘";
  }
  return koCode(value);
}

function manualSmokeTitle(smoke: ManualIngestSmoke) {
  if (smoke.status === "passed") {
    return "최근 수동 수집 smoke 성공";
  }
  if (smoke.status === "failed") {
    return "최근 수동 수집 smoke 실패";
  }
  if (smoke.status === "preview_not_executed") {
    return "수동 수집 계획만 확인됨";
  }
  if (smoke.status === "not_configured") {
    return "수동 수집 smoke 요약 미연결";
  }
  if (smoke.status === "missing_report") {
    return "수동 수집 smoke report 파일 없음";
  }
  return koCode(smoke.status);
}

function manualSmokeExplanation(smoke: ManualIngestSmoke) {
  if (smoke.status === "passed") {
    return "market/news/AI 단발 작업이 artifact runner를 통해 실행됐고 실패 작업이 없다는 뜻이다. 반복 자동화가 켜졌다는 뜻은 아니다.";
  }
  if (smoke.status === "failed") {
    return "단발 실행 중 실패한 작업이 있다. artifact 경로의 stderr/metadata를 먼저 확인해야 한다.";
  }
  if (smoke.status === "preview_not_executed") {
    return "실제 DB write나 provider 호출 없이 실행 계획만 생성한 상태다. 무료 API quota를 쓰지 않고 어떤 작업이 돌지 확인한 것이다.";
  }
  if (smoke.status === "not_configured") {
    return "FastAPI runtime에 STOCKANALYSIS_MANUAL_LOCAL_INGEST_SMOKE_REPORT가 연결되지 않았다. CLI 결과가 아직 화면으로 연결되지 않은 상태다.";
  }
  if (smoke.status === "missing_report") {
    return "환경변수는 설정됐지만 해당 요약 파일을 읽을 수 없다. repo 밖 경로에 summary를 다시 생성해야 한다.";
  }
  return "수동 수집 smoke 상태를 확인하려면 report 형식과 생성 시각을 점검해야 한다.";
}

function manualSmokeNextAction(smoke: ManualIngestSmoke) {
  return smoke.next_actions[0] ? koCode(smoke.next_actions[0]) : "다음 조치 없음";
}

function localWorkerTitle(worker: LocalIngestWorker) {
  if (worker.status === "completed") {
    return "로컬 worker 최근 실행 성공";
  }
  if (worker.status === "failed") {
    return "로컬 worker 최근 실행 실패";
  }
  if (worker.status === "preview_not_executed") {
    return "로컬 worker 계획만 확인됨";
  }
  if (worker.status === "not_configured") {
    return "로컬 worker report 미연결";
  }
  if (worker.status === "missing_report") {
    return "로컬 worker report 파일 없음";
  }
  return koCode(worker.status);
}

function localWorkerExplanation(worker: LocalIngestWorker) {
  if (worker.status === "completed") {
    return "local-ingest-worker-run이 bounded cycle을 끝냈고 실패 cycle이 없다는 뜻이다. 이 증거는 scheduler 설치와 별개로 로컬 반복 실행 가능성을 보여준다.";
  }
  if (worker.status === "failed") {
    return "worker cycle 중 실패가 있었다. 최신 smoke summary와 artifact stderr를 먼저 확인해야 한다.";
  }
  if (worker.status === "preview_not_executed") {
    return "실제 DB write나 provider 호출 없이 worker 실행 계획만 확인한 상태다.";
  }
  if (worker.status === "not_configured") {
    return "FastAPI runtime에 STOCKANALYSIS_LOCAL_INGEST_WORKER_REPORT가 연결되지 않아 worker 상태를 화면에서 읽을 수 없다.";
  }
  if (worker.status === "missing_report") {
    return "환경변수는 설정됐지만 worker summary 파일을 읽을 수 없다. repo 밖 output report를 다시 생성해야 한다.";
  }
  return "worker 상태를 판단하려면 report 형식과 생성 시각을 점검해야 한다.";
}

function localWorkerNextAction(worker: LocalIngestWorker) {
  return worker.next_actions[0] ? koCode(worker.next_actions[0]) : "다음 조치 없음";
}

const DEFAULT_MANUAL_SMOKE: ManualIngestSmoke = {
  status: "not_configured",
  execute: false,
  generated_at: "",
  runtime_status: "",
  artifact_root: "",
  job_count: 0,
  planned_job_ids: [],
  artifact_runs: [],
  failed_job_count: 0,
  next_actions: ["run manual-local-ingest-smoke --output outside the repository"],
  source: "not_configured",
};

const DEFAULT_LOCAL_WORKER: LocalIngestWorker = {
  status: "not_configured",
  execute: false,
  generated_at: "",
  completed_cycle_count: 0,
  failed_cycle_count: 0,
  max_cycles: 0,
  interval_seconds: 0,
  stop_on_failure: true,
  job_ids: [],
  latest_smoke_output_path: "",
  cycles: [],
  next_actions: ["run local-ingest-worker-run --output outside the repository"],
  source: "not_configured",
};

export default async function DataHealthPage() {
  const response = await getDataHealth();
  const data = response.data;
  const providerBudget = data.provider_budget;
  const schedulerActivation = data.scheduler.activation;
  const manualSmoke = data.manual_local_ingest_smoke ?? DEFAULT_MANUAL_SMOKE;
  const localWorker = data.local_ingest_worker ?? DEFAULT_LOCAL_WORKER;
  const marketPriceRun = findPipelineRun(data, "market-price-daily", "market_price_upsert");
  const newsRun = findPipelineRun(data, "news-rss-daily", "news_rss_upsert");
  const aiRun = findPipelineRun(data, "event-intelligence-weekly", "event_intelligence_llm_extract");
  const budgetUsage =
    providerBudget.daily_budget > 0
      ? Math.round((providerBudget.used_request_count / providerBudget.daily_budget) * 100)
      : 0;
  const failedPipelines = data.pipeline_runs.filter((run) => run.latest_status !== "succeeded").length;
  const automationCards = [
    {
      title: "주식 캔들 수집",
      run: marketPriceRun,
      fallbackCadence: "일간 · 18:30",
      description: "무료 가격 provider 예산을 확인한 뒤 일봉 캔들을 DB에 저장한다.",
      detail: `최근 가격 관측일 ${data.freshness.find((item) => item.dataset === "market.daily_price_bar")?.latest_observation_date ?? "미확인"} · provider ${koCode(providerBudget.provider)}`,
    },
    {
      title: "뉴스 수집",
      run: newsRun,
      fallbackCadence: "일간 · 08:30",
      description: "repo 밖 RSS 설정의 무료 RSS/Atom feed를 읽고 원천 문서와 이벤트 원장에 저장한다.",
      detail: "뉴스는 이벤트, 종목 상세, 분석 지도, 추천 근거 점검으로 연결된다.",
    },
    {
      title: "AI 분석",
      run: aiRun,
      fallbackCadence: "주간 · Monday 09:00",
      description: "수집 문서를 구조화하고 AI 근거 artifact를 남긴다. 뉴스 묶음은 무료 로컬 규칙 기반이다.",
      detail: "AI는 근거를 정리하지만 매수·매도·주문 결론을 자동 실행하지 않는다.",
    },
  ];

  return (
    <div className="terminal-page">
      <section className="page-hero reveal" aria-labelledby="data-health-title">
        <div>
          <div className="bento-badge">Index 01 — 데이터 수집</div>
          <h1 className="page-title" id="data-health-title">
            데이터가 언제, 어디서, 얼마나 들어왔는지 확인한다.
          </h1>
        </div>
        <p className="page-lede">
          반복 실행 준비도, 파이프라인 실행 이력, 오래된 데이터셋, 무료 API 호출 예산을
          투자 운영 리스크로 직접 표시한다. 이 화면이 정상이 아니면 추천과 성과 해석도
          신뢰하지 않는다.
        </p>
      </section>

      <section className="status-rail compact-rail reveal delay-1" aria-label="데이터 상태 요약">
        <article className="rail-cell">
          <span>01 전체 상태</span>
          <strong>{koCode(data.overall_status)}</strong>
          <small>{data.as_of_date}</small>
        </article>
        <article className="rail-cell rail-critical">
          <span>02 실패 파이프라인</span>
          <strong>{failedPipelines}</strong>
          <small>{data.pipeline_runs.length}개 중</small>
        </article>
        <article className="rail-cell">
          <span>03 반복 실행</span>
          <strong>{automationStateLabel(schedulerActivation)}</strong>
          <small>{schedulerActivation.job_id ? koCode(schedulerActivation.job_id) : "gate 미설정"}</small>
        </article>
        <article className="rail-cell">
          <span>04 열린 관문</span>
          <strong>{data.open_gates.length}</strong>
          <small>운영 전제</small>
        </article>
        <article className="rail-cell">
          <span>05 호출 예산</span>
          <strong className="rail-ratio-value">
            {providerBudget.remaining_request_count}/{providerBudget.daily_budget}
          </strong>
          <small>{koCode(providerBudget.provider)}</small>
        </article>
      </section>

      <section className="flow-panel reveal delay-2" aria-labelledby="automation-summary-title">
        <div className="section-heading flow-heading">
          <span>자동 수집 / 분석 상태</span>
          <h2 id="automation-summary-title">최근 실행과 실제 반복 자동화를 분리해서 본다</h2>
        </div>
        <p className="page-lede" style={{ marginTop: 0, maxWidth: "980px" }}>
          아래 3개 작업은 최근 실행 이력 기준으로는 성공 상태다. 다만 현재 반복 실행은{" "}
          {automationStateLabel(schedulerActivation)} 상태라서, 자동 반복 실행이 켜졌다고 보지는 않는다.
        </p>

        <article className="ledger-panel" style={{ marginTop: "18px" }}>
          <div className="section-heading stacked-heading">
            <span>로컬 반복 실행 판단</span>
            <h3>{schedulerReadinessTitle(data.scheduler)}</h3>
          </div>
          <p style={{ color: "var(--text-secondary)", marginBottom: "16px" }}>
            {schedulerReadinessExplanation(data.scheduler)}
          </p>
          <dl className="fact-list compact-facts">
            <div>
              <dt>승인 관문</dt>
              <dd>{schedulerApprovalGateLabel(schedulerActivation.approval_gate)}</dd>
            </div>
            <div>
              <dt>활성화 허용</dt>
              <dd>{schedulerActivation.activation_allowed ? "예" : "아니오"}</dd>
            </div>
            <div>
              <dt>반복 실행 상태</dt>
              <dd>{schedulerInstallLabel(schedulerActivation.scheduler_activation)}</dd>
            </div>
            <div>
              <dt>근거 생성 시각</dt>
              <dd>{schedulerActivation.generated_at || "미확인"}</dd>
            </div>
            <div>
              <dt>증거 위치</dt>
              <dd>{data.scheduler.latest_artifact_root || "증거 경로 없음"}</dd>
            </div>
            <div>
              <dt>다음 조치</dt>
              <dd>{schedulerNextStepLabel(schedulerActivation)}</dd>
            </div>
          </dl>
        </article>

        <article className="ledger-panel" style={{ marginTop: "18px" }}>
          <div className="section-heading stacked-heading">
            <span>목표 운영 구조</span>
            <h3>웹 요청 서버가 아니라 operations worker가 수집을 실행한다</h3>
          </div>
          <p style={{ color: "var(--text-secondary)", marginBottom: "16px" }}>
            FastAPI와 Next.js는 화면 요청을 처리한다. 데이터 수집·뉴스 분석·성과 측정은
            로컬에서 수동 실행하거나, 나중에 로컬 반복 실행기가 `stockanalysis-operations` worker를 호출한다.
          </p>
          <dl className="fact-list compact-facts">
            <div>
              <dt>화면</dt>
              <dd>Next.js cockpit</dd>
            </div>
            <div>
              <dt>읽기 API</dt>
              <dd>FastAPI read-only backend</dd>
            </div>
            <div>
              <dt>작업 실행</dt>
              <dd>local manual run / local runner → stockanalysis-operations worker</dd>
            </div>
            <div>
              <dt>상태 저장</dt>
              <dd>Postgres pipeline run history + artifact storage</dd>
            </div>
          </dl>
        </article>

        <article className="ledger-panel" style={{ marginTop: "18px" }}>
          <div className="section-heading stacked-heading">
            <span>로컬 worker 실행 증거</span>
            <h3>{localWorkerTitle(localWorker)}</h3>
          </div>
          <p style={{ color: "var(--text-secondary)", marginBottom: "16px" }}>
            {localWorkerExplanation(localWorker)}
          </p>
          <dl className="fact-list compact-facts">
            <div>
              <dt>상태</dt>
              <dd>{koCode(localWorker.status)}</dd>
            </div>
            <div>
              <dt>실행 여부</dt>
              <dd>{localWorker.execute ? "실제 실행" : "미리보기"}</dd>
            </div>
            <div>
              <dt>생성 시각</dt>
              <dd>{localWorker.generated_at || "기록 없음"}</dd>
            </div>
            <div>
              <dt>완료 cycle</dt>
              <dd>
                {localWorker.completed_cycle_count}/{localWorker.max_cycles || localWorker.completed_cycle_count}회
              </dd>
            </div>
            <div>
              <dt>실패 cycle</dt>
              <dd>{localWorker.failed_cycle_count}회</dd>
            </div>
            <div>
              <dt>실패 시 중단</dt>
              <dd>{localWorker.stop_on_failure ? "예" : "아니오"}</dd>
            </div>
            <div>
              <dt>대상 작업</dt>
              <dd>
                {localWorker.job_ids.length > 0
                  ? localWorker.job_ids.map((jobId) => koCode(jobId)).join(" · ")
                  : "연결된 작업 없음"}
              </dd>
            </div>
            <div>
              <dt>최신 smoke 요약</dt>
              <dd>{localWorker.latest_smoke_output_path || "요약 경로 없음"}</dd>
            </div>
            <div>
              <dt>다음 조치</dt>
              <dd>{localWorkerNextAction(localWorker)}</dd>
            </div>
          </dl>
          {localWorker.cycles.length > 0 ? (
            <div className="ledger-table-wrap" style={{ marginTop: "16px" }}>
              <table className="ledger-table data-health-table">
                <thead>
                  <tr>
                    <th scope="col">Cycle</th>
                    <th scope="col">Smoke 상태</th>
                    <th scope="col">작업</th>
                    <th scope="col">Artifact</th>
                  </tr>
                </thead>
                <tbody>
                  {localWorker.cycles.map((cycle) => (
                    <tr key={`${cycle.cycle_number}-${cycle.started_at}`}>
                      <td>
                        <strong>{cycle.cycle_number}</strong>
                        <small>{cycle.started_at || "시각 없음"}</small>
                      </td>
                      <td>{koCode(cycle.smoke_status)}</td>
                      <td>
                        {cycle.job_count}개 · 실패 {cycle.failed_job_count}개
                      </td>
                      <td>{cycle.artifact_run_count}개</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : null}
        </article>

        <article className="ledger-panel" style={{ marginTop: "18px" }}>
          <div className="section-heading stacked-heading">
            <span>수동 단발 실행 증거</span>
            <h3>{manualSmokeTitle(manualSmoke)}</h3>
          </div>
          <p style={{ color: "var(--text-secondary)", marginBottom: "16px" }}>
            {manualSmokeExplanation(manualSmoke)}
          </p>
          <dl className="fact-list compact-facts">
            <div>
              <dt>상태</dt>
              <dd>{koCode(manualSmoke.status)}</dd>
            </div>
            <div>
              <dt>실행 여부</dt>
              <dd>{manualSmoke.execute ? "실제 실행" : "미리보기"}</dd>
            </div>
            <div>
              <dt>생성 시각</dt>
              <dd>{manualSmoke.generated_at || "기록 없음"}</dd>
            </div>
            <div>
              <dt>런타임 상태</dt>
              <dd>{manualSmoke.runtime_status ? koCode(manualSmoke.runtime_status) : "미확인"}</dd>
            </div>
            <div>
              <dt>대상 작업</dt>
              <dd>
                {manualSmoke.planned_job_ids.length > 0
                  ? manualSmoke.planned_job_ids.map((jobId) => koCode(jobId)).join(" · ")
                  : "연결된 작업 없음"}
              </dd>
            </div>
            <div>
              <dt>실행 artifact</dt>
              <dd>
                {manualSmoke.artifact_runs.length}개 기록 · 실패 {manualSmoke.failed_job_count}개
              </dd>
            </div>
            <div>
              <dt>증거 위치</dt>
              <dd>{manualSmoke.artifact_root || "증거 경로 없음"}</dd>
            </div>
            <div>
              <dt>다음 조치</dt>
              <dd>{manualSmokeNextAction(manualSmoke)}</dd>
            </div>
          </dl>
          {manualSmoke.artifact_runs.length > 0 ? (
            <div className="ledger-table-wrap" style={{ marginTop: "16px" }}>
              <table className="ledger-table data-health-table">
                <thead>
                  <tr>
                    <th scope="col">작업</th>
                    <th scope="col">상태</th>
                    <th scope="col">종료 코드</th>
                    <th scope="col">stderr</th>
                  </tr>
                </thead>
                <tbody>
                  {manualSmoke.artifact_runs.map((run) => (
                    <tr key={`${run.job_id}-${run.artifact_dir || run.exit_code}`}>
                      <td>
                        <strong>{koCode(run.job_id)}</strong>
                        <small>{koCode(run.pipeline_name)}</small>
                      </td>
                      <td>{koCode(run.status)}</td>
                      <td>{run.exit_code}</td>
                      <td>{run.stderr_path || "없음"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : null}
        </article>

        <div className="flow-steps" style={{ marginTop: "18px" }}>
          {automationCards.map((card) => (
            <article className="flow-step" key={card.title}>
              <span>{card.title}</span>
              <strong>{runStateLabel(card.run)}</strong>
              <p>{card.description}</p>
              <dl className="fact-list compact-facts" style={{ marginTop: "14px" }}>
                <div>
                  <dt>반복 기준</dt>
                  <dd>{cadenceLabel(card.run, card.fallbackCadence)}</dd>
                </div>
                <div>
                  <dt>최근 완료</dt>
                  <dd>{finishedAtLabel(card.run)}</dd>
                </div>
                <div>
                  <dt>자동화</dt>
                  <dd>{automationStateLabel(schedulerActivation)}</dd>
                </div>
                <div>
                  <dt>사용처</dt>
                  <dd>{card.detail}</dd>
                </div>
              </dl>
            </article>
          ))}
        </div>
      </section>

      <section className="split-ledger reveal delay-2">
        <article className="ledger-panel queue-panel">
          <div className="section-heading">
            <span>Index 01.A — 파이프라인 실행</span>
            <h2>파이프라인 실행 이력</h2>
          </div>
          <div className="ledger-table-wrap">
            <table className="ledger-table data-health-table">
              <thead>
                <tr>
                  <th scope="col">파이프라인</th>
                  <th scope="col">도메인</th>
                  <th scope="col">상태</th>
                  <th scope="col">최신성</th>
                  <th scope="col">최근 실행</th>
                  <th scope="col">완료 시각</th>
                </tr>
              </thead>
              <tbody>
                {data.pipeline_runs.map((run) => (
                  <tr key={run.latest_run_id}>
                    <td>
                      <strong>{koCode(run.pipeline_name)}</strong>
                      <small>{koCode(run.cadence)}</small>
                    </td>
                    <td>{koCode(run.domain)}</td>
                    <td>
                      <span className={`risk-tag ${statusRiskClass(run.latest_status)}`}>
                        {koCode(run.latest_status)}
                      </span>
                    </td>
                    <td>{koCode(run.health_status)}</td>
                    <td>{run.latest_run_id}</td>
                    <td>{run.finished_at}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </article>

        <aside className="side-ledger">
          <article className="ledger-panel">
            <div className="section-heading stacked-heading">
              <span>Index 01.B — 무료 API 호출 예산</span>
              <h2>데이터 제공자 호출 예산</h2>
            </div>
            <div className="budget-meter" aria-label={`호출 예산 사용률 ${budgetUsage}%`}>
              <div style={{ width: `${Math.min(100, Math.max(0, budgetUsage))}%` }} />
            </div>
            <dl className="fact-list">
              <div>
                <dt>상태</dt>
                <dd>{koCode(providerBudget.status)}</dd>
              </div>
              <div>
                <dt>사용</dt>
                <dd>{providerBudget.used_request_count}회</dd>
              </div>
              <div>
                <dt>기준일</dt>
                <dd>{providerBudget.budget_date}</dd>
              </div>
              <div>
                <dt>최근 실행</dt>
                <dd>{providerBudget.latest_run?.started_at ?? "오늘 실행 없음"}</dd>
              </div>
            </dl>
          </article>

          <article className="ledger-panel">
            <div className="section-heading stacked-heading">
              <span>Index 01.C — 관문 / 최신성</span>
              <h2>관문과 데이터 최신성</h2>
            </div>
            <div className="tag-ledger">
              {data.open_gates.map((gate) => (
                <span className="risk-tag risk-medium" key={gate}>
                  {koCode(gate)}
                </span>
              ))}
            </div>
            <dl className="fact-list compact-facts">
              {data.freshness.map((item) => (
                <div key={item.dataset}>
                  <dt>{koCode(item.dataset)}</dt>
                  <dd>
                    {koCode(item.status)} · {item.latest_observation_date}
                  </dd>
                </div>
              ))}
            </dl>
          </article>

          <article className="ledger-panel">
            <div className="section-heading stacked-heading">
              <span>Index 01.D — 반복 실행</span>
              <h2>반복 실행 준비 상태</h2>
            </div>
            <dl className="fact-list">
              <div>
                <dt>자동 실행기</dt>
                <dd>{schedulerInstallLabel(data.scheduler.install_status)}</dd>
              </div>
              <div>
                <dt>환경</dt>
                <dd>{koCode(data.scheduler.runtime_env_readiness)}</dd>
              </div>
              <div>
                <dt>승인 상태</dt>
                <dd>{automationStateLabel(schedulerActivation)}</dd>
              </div>
              <div>
                <dt>대상 작업</dt>
                <dd>{koCode(schedulerActivation.job_id)}</dd>
              </div>
              <div>
                <dt>승인 관문</dt>
                <dd>{schedulerApprovalGateLabel(schedulerActivation.approval_gate)}</dd>
              </div>
              <div>
                <dt>활성화 가능</dt>
                <dd>{schedulerActivation.activation_allowed ? "예" : "아니오"}</dd>
              </div>
              <div>
                <dt>다음 단계</dt>
                <dd>{schedulerNextStepLabel(schedulerActivation)}</dd>
              </div>
              <div>
                <dt>휴장일 처리</dt>
                <dd>{koCode(data.scheduler.holiday_skip_mode)}</dd>
              </div>
            </dl>
          </article>
        </aside>
      </section>
    </div>
  );
}
