import { getDataHealth } from "@/lib/frontend-api";
import { koCode } from "@/lib/korean-labels";
import type { DataHealthData } from "@/lib/types";

export const dynamic = "force-dynamic";
export const metadata = { title: "데이터 수집" };

type PipelineRun = DataHealthData["pipeline_runs"][number];
type SchedulerActivation = DataHealthData["scheduler"]["activation"];
type SchedulerStatus = DataHealthData["scheduler"];
type ProfileSchedulerStatus = NonNullable<DataHealthData["scheduler"]["profile_scheduler"]>;
type ManualIngestSmoke = DataHealthData["manual_local_ingest_smoke"];
type LocalIngestWorker = DataHealthData["local_ingest_worker"];

function statusRiskClass(value: string) {
  if (value === "healthy" || value === "succeeded" || value === "configured" || value === "not_due") {
    return "risk-low";
  }
  if (
    value === "attention_required"
    || value === "stale"
    || value === "degraded"
    || value === "succeeded_with_fallback"
  ) {
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
  if (run.latest_status === "succeeded_with_fallback" || run.health_status === "degraded") {
    return "성공했지만 대체 처리 사용";
  }
  if (run.latest_status === "succeeded") {
    return `성공 · ${koCode(run.health_status)}`;
  }
  return `${koCode(run.latest_status)} · ${koCode(run.health_status)}`;
}

function automationStateLabel(schedulerActivation: SchedulerActivation) {
  if (schedulerActivation.activation_allowed) {
    return schedulerActivation.scheduler_activation === "installed" ? "자동 반복 실행 중" : "반복 실행 설정됨";
  }
  if (schedulerActivation.status === "pending_manual_approval") {
    return "자동 반복 실행 미설정";
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

function runQualityExplanation(run: PipelineRun | null) {
  if (!run) {
    return "실행 이력이 없어 품질을 판단할 수 없다.";
  }
  if (run.latest_status === "succeeded_with_fallback" || run.health_status === "degraded") {
    return "작업은 멈추지 않았지만 일부 AI 후보가 실패해 규칙 기반 대체 처리로 완료됐다. 추천 근거 품질을 낮게 보고 오류 로그를 확인해야 한다.";
  }
  if (run.latest_status === "succeeded" && run.health_status === "ok") {
    return "최근 실행은 정상 범위다.";
  }
  return "상태와 완료 시각을 기준으로 실행 로그를 확인해야 한다.";
}

function schedulerReadinessTitle(scheduler: SchedulerStatus) {
  const activation = scheduler.activation;
  if (activation.approval_gate === "installed_on_ec2_systemd") {
    return "EC2 systemd 반복 실행기 작동 중";
  }
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
  const profileScheduler = scheduler.profile_scheduler;
  if (activation.approval_gate === "installed_on_ec2_systemd") {
    const activeCount = profileScheduler?.active_timer_count ?? 0;
    const timerCount = profileScheduler?.timer_count ?? 0;
    return `EC2 서버의 systemd timer가 데이터 수집과 분석 작업을 주기별로 호출한다. 현재 반복 실행기는 ${activeCount}/${timerCount}개가 활성 상태다.`;
  }
  if (activation.activation_allowed && activation.scheduler_activation !== "not_installed") {
    return "승인 관문과 실행기 상태가 반복 실행을 허용한다. EC2 예약 실행기가 작업별 주기에 맞춰 수집과 분석을 호출한다.";
  }
  if (activation.status === "pending_manual_approval") {
    return "최근 파이프라인 실행은 성공했지만 자동 반복 실행기는 아직 연결되지 않았다. 이 상태에서는 사람이 수동으로 실행해야 데이터가 갱신된다.";
  }
  if (activation.status === "not_configured") {
    return "반복 실행 결과가 연결되지 않아 자동 실행 여부를 판단할 수 없다.";
  }
  if (activation.status === "invalid_report") {
    return "반복 실행 결과 형식이 맞지 않아 운영 근거로 사용할 수 없다.";
  }
  return "현재 반복 실행 상태는 화면의 승인 관문과 다음 단계 값을 기준으로 다시 확인해야 한다.";
}

function schedulerNextStepLabel(activation: SchedulerActivation) {
  if (activation.manual_next_step === "data-operations-live-scheduler-activation-request") {
    return "반복 실행 설정 전에 수동 수집 순서와 결과를 먼저 확인한다.";
  }
  if (activation.manual_next_step === "configure_scheduler_activation_gate_report") {
    return "저장소 밖 반복 실행 결과 경로를 설정한다.";
  }
  if (activation.manual_next_step === "regenerate_scheduler_activation_gate_report") {
    return "깨진 스케줄러 결과 파일을 다시 생성한다.";
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
    return "자동 반복 실행 전 관문 닫힘";
  }
  return koCode(value);
}

function manualSmokeTitle(smoke: ManualIngestSmoke) {
  if (smoke.status === "passed") {
    return "최근 수동 수집 성공";
  }
  if (smoke.status === "failed") {
    return "최근 수동 수집 실패";
  }
  if (smoke.status === "preview_not_executed") {
    return "수동 수집 계획만 확인됨";
  }
  if (smoke.status === "not_configured") {
    return "최근 수동 수집 결과 미연결";
  }
  if (smoke.status === "missing_report") {
    return "최근 수동 수집 결과 파일 없음";
  }
  return koCode(smoke.status);
}

function manualSmokeExplanation(smoke: ManualIngestSmoke) {
  if (smoke.status === "passed") {
    return "가격, 뉴스, AI 분석 단발 작업이 실행됐고 실패 작업이 없다는 뜻이다. 반복 자동화 상태는 별도로 확인한다.";
  }
  if (smoke.status === "failed") {
    return "단발 실행 중 실패한 작업이 있다. 실행 산출물의 오류 로그와 메타데이터를 먼저 확인해야 한다.";
  }
  if (smoke.status === "preview_not_executed") {
    return "실제 DB 저장이나 외부 데이터 제공자 호출 없이 실행 계획만 생성한 상태다. 무료 API 한도를 쓰지 않고 어떤 작업이 돌지 확인한 것이다.";
  }
  if (smoke.status === "not_configured") {
    return "백엔드에 최근 수동 수집 결과 경로가 연결되지 않아 화면에서 읽을 수 없다.";
  }
  if (smoke.status === "missing_report") {
    return "환경변수는 설정됐지만 해당 요약 파일을 읽을 수 없다. 저장소 밖 경로에 요약 파일을 다시 생성해야 한다.";
  }
    return "수동 수집 상태를 확인하려면 결과 파일 형식과 생성 시각을 점검해야 한다.";
}

function manualSmokeNextAction(smoke: ManualIngestSmoke) {
  return smoke.next_actions[0] ? koCode(smoke.next_actions[0]) : "다음 조치 없음";
}

function localWorkerTitle(worker: LocalIngestWorker) {
  if (worker.status === "completed") {
    return "반복 실행 최근 성공";
  }
  if (worker.status === "failed") {
    return "반복 실행 최근 실패";
  }
  if (worker.status === "preview_not_executed") {
    return "반복 실행 계획만 확인됨";
  }
  if (worker.status === "not_configured") {
    return "반복 실행 결과 미연결";
  }
  if (worker.status === "missing_report") {
    return "반복 실행 결과 파일 없음";
  }
  return koCode(worker.status);
}

function localWorkerExplanation(worker: LocalIngestWorker) {
  if (worker.status === "completed") {
    return "정해진 반복 실행 주기가 끝났고 실패 주기가 없다는 뜻이다. EC2의 예약 실행과 함께 자동 운영 상태를 판단한다.";
  }
  if (worker.status === "failed") {
    return "반복 실행 중 실패가 있었다. 최신 실행 요약과 오류 로그를 먼저 확인해야 한다.";
  }
  if (worker.status === "preview_not_executed") {
    return "실제 DB 저장이나 외부 데이터 제공자 호출 없이 반복 실행 계획만 확인한 상태다.";
  }
  if (worker.status === "not_configured") {
    return "백엔드에 반복 실행 결과 경로가 연결되지 않아 화면에서 읽을 수 없다.";
  }
  if (worker.status === "missing_report") {
    return "환경변수는 설정됐지만 반복 실행 결과 파일을 읽을 수 없다. 저장소 밖 경로에 결과를 다시 생성해야 한다.";
  }
  return "반복 실행 상태를 판단하려면 결과 파일 형식과 생성 시각을 점검해야 한다.";
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

const DEFAULT_PROFILE_SCHEDULER: ProfileSchedulerStatus = {
  status: "not_configured",
  install_status: "not_installed",
  scheduler_type: "",
  timer_count: 0,
  active_timer_count: 0,
  generated_at: "",
  source: "not_configured",
  timers: [],
};

export default async function DataHealthPage() {
  const response = await getDataHealth();
  const data = response.data;
  const providerBudget = data.provider_budget;
  const schedulerActivation = data.scheduler.activation;
  const profileScheduler = data.scheduler.profile_scheduler ?? DEFAULT_PROFILE_SCHEDULER;
  const manualSmoke = data.manual_local_ingest_smoke ?? DEFAULT_MANUAL_SMOKE;
  const localWorker = data.local_ingest_worker ?? DEFAULT_LOCAL_WORKER;
  const marketPriceRun = findPipelineRun(data, "market-price-daily", "market_price_upsert");
  const newsRun = findPipelineRun(data, "news-rss-daily", "news_rss_upsert");
  const newsEnrichmentRun = findPipelineRun(
    data,
    "news-rss-enrichment-intraday",
    "news_rss_event_enrichment",
  );
  const aiRun = findPipelineRun(data, "event-intelligence-weekly", "event_intelligence_llm_extract");
  const decisionRun = findPipelineRun(data, "cycle-recommendation-weekly", "cycle_state_snapshot");
  const remediationRun = findPipelineRun(
    data,
    "portfolio-remediation-daily",
    "portfolio_remediation_daily_automation",
  );
  const budgetUsage =
    providerBudget.daily_budget > 0
      ? Math.round((providerBudget.used_request_count / providerBudget.daily_budget) * 100)
      : 0;
  const failedPipelines = data.pipeline_runs.filter((run) =>
    ["missing", "stale", "failed"].includes(run.health_status),
  ).length;
  const automationCards = [
    {
      title: "주식 캔들 수집",
      run: marketPriceRun,
      fallbackCadence: "일간 · 18:30",
      description: "무료 가격 데이터 제공자의 한도를 확인한 뒤 일봉 캔들을 DB에 저장한다.",
      detail: `최근 가격 관측일 ${data.freshness.find((item) => item.dataset === "market.daily_price_bar")?.latest_observation_date ?? "미확인"} · 제공자 ${koCode(providerBudget.provider)}`,
    },
    {
      title: "뉴스 수집",
      run: newsRun,
      fallbackCadence: "일간 · 08:30",
      description: "저장소 밖 RSS 설정의 무료 뉴스 피드를 읽고 원천 문서와 이벤트 원장에 저장한다.",
      detail: "뉴스는 이벤트, 종목 상세, 분석 지도, 추천 근거 점검으로 연결된다.",
    },
    {
      title: "AI 분석",
      run: aiRun,
      fallbackCadence: "장중 · 2시간마다",
      description: "수집 문서를 구조화하고 AI 근거 기록을 남긴다. 중요 뉴스는 Codex OAuth 배치 후보로 분석하고, 뉴스 묶음은 무료 로컬 규칙 보조 증거로 남긴다.",
      detail: "AI는 근거를 정리하지만 매수·매도·주문 결론을 자동 실행하지 않는다.",
    },
  ];
  const newsAfterAnalysisSteps = [
    {
      index: "01",
      title: "뉴스 원문 수집",
      run: newsRun,
      owner: "news-rss-daily",
      output: "RSS/Atom 문서를 원천 문서 테이블과 실행 증거 기록에 저장한다.",
      next: "중복과 원천 링크를 남긴 뒤 이벤트 구조화 단계로 넘긴다.",
    },
    {
      index: "02",
      title: "이벤트 구조화",
      run: newsEnrichmentRun,
      owner: "news-rss-enrichment-intraday",
      output: "헤드라인과 본문을 종목·테마·영향 방향이 있는 `event.event`로 정리한다.",
      next: "동일 테마/종목 관계를 만들고 `/events`, `/stocks`, `/intelligence`가 읽는다.",
    },
    {
      index: "03",
      title: "AI 근거 생성",
      run: aiRun,
      owner: "event-intelligence-weekly",
      output: "중요 뉴스만 Codex OAuth 배치로 분석해 종목·테마·방향·근거 후보를 AI 추출 기록에 남긴다.",
      next: "검증기를 통과한 근거만 표준 이벤트 영향으로 반영한다. 매수·매도·주문 결론은 여기서 만들지 않는다.",
    },
    {
      index: "04",
      title: "신호와 추천 후보 갱신",
      run: decisionRun,
      owner: "decision-daily",
      output: "가격, 테마 연결, 이벤트 강도, 사이클 상태를 합쳐 추천 후보와 투자 논리 입력을 만든다.",
      next: "결정 로직은 재현 가능한 점수 계산이다. AI 근거는 설명 가능한 보조 근거로 붙는다.",
    },
    {
      index: "05",
      title: "보유 검토와 운영 큐",
      run: remediationRun,
      owner: "portfolio-remediation-daily",
      output: "보유 투자 논리 유지 여부, 빈 가격/논리/성과 항목, 가상 거래 검증 문제를 큐로 만든다.",
      next: "추천, 투자 논리, 보유 검토, 가상 거래 화면에서 사람이 검토한다.",
    },
  ];
  const collectionStatusCards = [
    {
      index: "01",
      title: "주식 캔들",
      run: marketPriceRun,
      purpose: "종목 가격과 차트, 모멘텀 feature의 원천이다.",
      check: `최근 가격일 ${
        data.freshness.find((item) => item.dataset === "market.daily_price_bar")?.latest_observation_date ?? "미확인"
      }`,
    },
    {
      index: "02",
      title: "뉴스 원문",
      run: newsRun,
      purpose: "수집된 뉴스 원장과 원천 문서 화면의 원천이다.",
      check: "뉴스 원장은 /events에서 시간순으로 본다.",
    },
    {
      index: "03",
      title: "1차 분류 태깅",
      run: newsEnrichmentRun,
      purpose: "뉴스를 종목, 테마, 방향 태그로 1차 정리한다.",
      check: "AI 전 단계이므로 틀릴 수 있고, 이후 AI/validator가 보강한다.",
    },
    {
      index: "04",
      title: "Codex OAuth 분석",
      run: aiRun,
      purpose: "중요 뉴스를 구조화해 근거 후보를 만든다.",
      check: "화면 요청 중에는 LLM을 호출하지 않고 저장된 결과만 읽는다.",
    },
    {
      index: "05",
      title: "Validator",
      run: aiRun,
      purpose: "낮은 신뢰도, 알 수 없는 종목/테마, 저신호 뉴스를 차단한다.",
      check: "차단 후보는 /ai-evidence의 차단 섹션에서 본다.",
    },
    {
      index: "06",
      title: "추천 신호",
      run: decisionRun,
      purpose: "가격, 뉴스, 사이클, 상위 흐름을 추천 점수로 합친다.",
      check: "추천은 주문이 아니라 사람이 볼 검토서다.",
    },
    {
      index: "07",
      title: "보유 검토",
      run: remediationRun,
      purpose: "Thesis 공백, 성과 미측정, 보유 충돌을 운영 큐로 만든다.",
      check: "보유 검토와 paper 검증으로 이어진다.",
    },
  ];

  return (
    <div className="terminal-page">
      <section className="page-hero reveal" aria-labelledby="data-health-title">
        <div>
          <div className="bento-badge">데이터 수집 상태</div>
          <h1 className="page-title" id="data-health-title">
            데이터 수집과 자동 실행이 정상인지 먼저 확인한다.
          </h1>
        </div>
        <p className="page-lede">
          뉴스는 짧은 주기, 주식 캔들은 장 마감 후, 추천·보유검토는 데이터 보강 뒤에 돈다.
          이 화면이 정상이 아니면 추천과 성과 해석도 신뢰하지 않는다.
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

      <section className="feature-map-panel reveal delay-1" aria-labelledby="collection-status-title">
        <div className="section-heading stacked-heading">
          <span>수집/분석별 상태</span>
          <h2 id="collection-status-title">무엇이 언제 돌았고, 어디에 쓰이는지 한 번에 본다</h2>
        </div>
        <p className="board-intro">
          이 영역만 보면 “어떤 데이터가 최신인지”를 먼저 판단할 수 있다. 아래 상세 증거는 문제가 있을 때만 펼쳐서 본다.
        </p>
        <div className="feature-map-grid collection-map-grid">
          {collectionStatusCards.map((card) => (
            <article className="feature-map-card collection-map-card" key={card.index}>
              <span>{card.index}</span>
              <strong>{card.title}</strong>
              <em className={`risk-tag ${statusRiskClass(card.run?.health_status ?? "missing")}`}>
                {runStateLabel(card.run)}
              </em>
              <small>{card.purpose}</small>
              <small>{card.check}</small>
              <small>최근 완료: {finishedAtLabel(card.run)}</small>
            </article>
          ))}
        </div>
      </section>

      {aiRun?.health_status === "degraded" || aiRun?.latest_status === "succeeded_with_fallback" ? (
        <section className="flow-panel reveal delay-1" aria-labelledby="ai-fallback-warning-title">
          <div className="section-heading flow-heading">
            <span>AI 분석 경고</span>
            <h2 id="ai-fallback-warning-title">뉴스 AI 분석이 대체 처리로 끝난 실행이 있다</h2>
          </div>
          <p className="page-lede" style={{ marginTop: 0, maxWidth: "980px" }}>
            {runQualityExplanation(aiRun)} 이 상태에서는 뉴스 수집과 이벤트 구조화는 계속 진행되지만,
            LLM이 만든 한국어 근거와 종목·테마 영향 검증 품질은 낮아질 수 있다.
          </p>
        </section>
      ) : null}

      <section className="flow-panel reveal delay-2" aria-labelledby="automation-summary-title">
        <div className="section-heading flow-heading">
          <span>자동 수집 / 분석 상태</span>
          <h2 id="automation-summary-title">최근 실행과 실제 반복 자동화를 분리해서 본다</h2>
        </div>
        <p className="page-lede" style={{ marginTop: 0, maxWidth: "980px" }}>
          아래 작업은 최근 실행 이력과 반복 실행 상태를 같이 보여준다. 현재 반복 실행은{" "}
          {automationStateLabel(schedulerActivation)} 상태이며, 수집 성공과 추천 품질은 별도로 검토한다.
        </p>

        <article className="ledger-panel" style={{ marginTop: "18px" }}>
          <div className="section-heading stacked-heading">
            <span>자동 반복 실행 상태</span>
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
            <span>실제 실행 구조</span>
            <h3>웹 화면은 읽고, EC2 예약 작업이 수집·분석을 실행한다</h3>
          </div>
          <p style={{ color: "var(--text-secondary)", marginBottom: "16px" }}>
            FastAPI와 Next.js는 저장된 결과를 읽어 보여준다. 뉴스 수집, 캔들 보강, AI 분석, 추천 갱신은
            EC2 systemd timer가 백그라운드 작업 실행기를 호출해 수행하고, 결과는 Postgres와 증거 파일에 남긴다.
          </p>
          <dl className="fact-list compact-facts">
            <div>
              <dt>화면</dt>
              <dd>Next.js 운영 화면</dd>
            </div>
            <div>
              <dt>읽기 API</dt>
              <dd>FastAPI 읽기 전용 백엔드</dd>
            </div>
            <div>
              <dt>작업 실행</dt>
              <dd>EC2 예약 실행 → 백그라운드 작업 실행기</dd>
            </div>
            <div>
              <dt>상태 저장</dt>
              <dd>Postgres 실행 이력 + 저장소 밖 증거 파일</dd>
            </div>
          </dl>
        </article>

        <article className="ledger-panel" style={{ marginTop: "18px" }}>
          <div className="section-heading stacked-heading">
            <span>EC2 systemd 반복 실행기</span>
            <h3>
              {profileScheduler.active_timer_count}/{profileScheduler.timer_count}개 profile timer 활성
            </h3>
          </div>
          <p style={{ color: "var(--text-secondary)", marginBottom: "16px" }}>
            수집기는 하나로 묶여 있지 않다. 뉴스/AI는 짧은 주기, 캔들은 장 마감 후, 신호/추천은 캔들 이후,
            거시·SEC·성과는 느린 주기로 분리되어 돈을 아끼면서도 필요한 데이터가 갱신되게 한다.
          </p>
          <div className="scheduler-timer-grid">
            {profileScheduler.timers.map((timer) => (
              <div className="scheduler-timer-card" key={timer.profile_id}>
                <span>{koCode(timer.profile_id)}</span>
                <strong>{koCode(timer.active_state)}</strong>
                <small>{timer.schedule || "스케줄 미확인"}</small>
                <dl>
                  <div>
                    <dt>다음 실행</dt>
                    <dd>{timer.next_elapse || "미확인"}</dd>
                  </div>
                  <div>
                    <dt>마지막 결과</dt>
                    <dd>{koCode(timer.last_result || "unknown")}</dd>
                  </div>
                </dl>
              </div>
            ))}
          </div>
        </article>

        <article className="ledger-panel" style={{ marginTop: "18px" }}>
          <div className="section-heading stacked-heading">
            <span>뉴스 분석 이후 운영 흐름</span>
            <h3>AI 근거 이후에는 추천·투자 논리·보유 검토로 넘어간다</h3>
          </div>
          <p style={{ color: "var(--text-secondary)", marginBottom: "16px" }}>
            뉴스 분석은 끝점이 아니다. 수집된 뉴스는 이벤트와 AI 근거가 되고, 이후 가격·테마·사이클 데이터와
            결합되어 중장기 추천 후보, 투자 논리, 보유 검토 큐를 만든다. 주문은 자동 실행하지 않는다.
          </p>
          <div className="operating-flow-grid">
            {newsAfterAnalysisSteps.map((step) => (
            <div className="operating-flow-card" key={step.index}>
              <b>{step.index}</b>
              <span>{koCode(step.owner)}</span>
              <strong>{step.title}</strong>
              <p>{step.output}</p>
              <small>{step.next}</small>
              {step.run?.health_status === "degraded" || step.run?.latest_status === "succeeded_with_fallback" ? (
                <small>{runQualityExplanation(step.run)}</small>
              ) : null}
              <dl>
                  <div>
                    <dt>상태</dt>
                    <dd>{runStateLabel(step.run)}</dd>
                  </div>
                  <div>
                    <dt>최근 완료</dt>
                    <dd>{finishedAtLabel(step.run)}</dd>
                  </div>
                </dl>
              </div>
            ))}
          </div>
        </article>

        <article className="ledger-panel" style={{ marginTop: "18px" }}>
          <div className="section-heading stacked-heading">
            <span>최근 자동 실행 증거</span>
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
              <dt>완료 회차</dt>
              <dd>
                {localWorker.completed_cycle_count}/{localWorker.max_cycles || localWorker.completed_cycle_count}회
              </dd>
            </div>
            <div>
              <dt>실패 회차</dt>
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
              <dt>최신 수집 요약</dt>
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
                    <th scope="col">회차</th>
                    <th scope="col">실행 검증</th>
                    <th scope="col">작업</th>
                    <th scope="col">증거 기록</th>
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
            <span>최근 수동 점검 증거</span>
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
              <dt>실행 증거</dt>
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

        <div className="flow-steps data-health-summary-grid" style={{ marginTop: "18px" }}>
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
            <span>실행 이력</span>
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
              <span>무료 API 예산</span>
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
              <span>관문과 최신성</span>
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
              <span>자동 반복 실행</span>
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
