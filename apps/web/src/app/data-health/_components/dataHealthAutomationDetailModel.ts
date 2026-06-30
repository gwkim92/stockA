import type { DataHealthAutomationDetailSectionProps } from "@/components/operations/DataHealthAutomationDetailTypes";
import { koCode } from "@/lib/korean-labels";

import {
  buildLocalWorkerPanel,
  buildManualSmokePanel,
} from "./dataHealthAutomationEvidencePanelModel";
import {
  automationStateLabel,
  cadenceLabel,
  evidenceLocationLabel,
  finishedAtLabel,
  runQualityExplanation,
  runStateLabel,
  schedulerApprovalGateLabel,
  schedulerInstallLabel,
  schedulerNextStepLabel,
  schedulerReadinessExplanation,
  schedulerReadinessTitle,
} from "./dataHealthModel";
import type {
  DataHealthData,
  LocalIngestWorker,
  ManualIngestSmoke,
  PipelineRun,
  ProfileSchedulerStatus,
  SchedulerActivation,
} from "./dataHealthTypes";

type DataHealthPipelineRuns = {
  readonly aiRun: PipelineRun | null;
  readonly decisionRun: PipelineRun | null;
  readonly marketPriceRun: PipelineRun | null;
  readonly newsEnrichmentRun: PipelineRun | null;
  readonly newsRun: PipelineRun | null;
  readonly remediationRun: PipelineRun | null;
};

type DataHealthAutomationDetailInput = {
  readonly data: DataHealthData;
  readonly ec2SchedulerInstalled: boolean;
  readonly localWorker: LocalIngestWorker;
  readonly manualSmoke: ManualIngestSmoke;
  readonly profileScheduler: ProfileSchedulerStatus;
  readonly provider: string;
  readonly runs: DataHealthPipelineRuns;
  readonly schedulerActivation: SchedulerActivation;
};

type DataHealthAutomationCardSource = {
  readonly description: string;
  readonly detail: string;
  readonly fallbackCadence: string;
  readonly run: PipelineRun | null;
  readonly title: string;
};

type DataHealthNewsAfterAnalysisStepSource = {
  readonly index: string;
  readonly next: string;
  readonly output: string;
  readonly owner: string;
  readonly run: PipelineRun | null;
  readonly title: string;
};

export function buildDataHealthAutomationDetailSection({
  data,
  ec2SchedulerInstalled,
  localWorker,
  manualSmoke,
  profileScheduler,
  provider,
  runs,
  schedulerActivation,
}: DataHealthAutomationDetailInput): DataHealthAutomationDetailSectionProps {
  return {
    automationCards: buildAutomationCardSources(data, provider, runs).map((card) => ({
      cadenceLabel: cadenceLabel(card.run, card.fallbackCadence),
      description: card.description,
      detail: card.detail,
      finishedAtLabel: finishedAtLabel(card.run),
      stateLabel: runStateLabel(card.run),
      title: card.title,
    })),
    automationStatusLabel: automationStateLabel(schedulerActivation),
    localWorker: buildLocalWorkerPanel(localWorker, ec2SchedulerInstalled),
    manualSmoke: buildManualSmokePanel(manualSmoke, ec2SchedulerInstalled),
    newsAfterAnalysisSteps: buildNewsAfterAnalysisStepSources(runs).map((step) => ({
      finishedAtLabel: finishedAtLabel(step.run),
      index: step.index,
      next: step.next,
      output: step.output,
      ownerLabel: koCode(step.owner),
      statusLabel: runStateLabel(step.run),
      title: step.title,
      warningLabel:
        step.run?.health_status === "degraded" || step.run?.latest_status === "succeeded_with_fallback"
          ? runQualityExplanation(step.run)
          : "",
    })),
    profileScheduler: {
      activeTimerSummaryLabel: `${profileScheduler.active_timer_count}/${profileScheduler.timer_count}개 예약 실행 활성`,
      timers: profileScheduler.timers.map((timer) => ({
        activeStateLabel: koCode(timer.active_state),
        lastResultLabel: koCode(timer.last_result || "unknown"),
        nextElapseLabel: timer.next_elapse || "미확인",
        profileLabel: koCode(timer.profile_id),
        scheduleLabel: timer.schedule || "스케줄 미확인",
      })),
    },
    schedulerDetail: {
      description: schedulerReadinessExplanation(data.scheduler),
      factRows: [
        { label: "승인 조건", value: schedulerApprovalGateLabel(schedulerActivation.approval_gate) },
        { label: "활성화 허용", value: schedulerActivation.activation_allowed ? "예" : "아니오" },
        { label: "반복 실행 상태", value: schedulerInstallLabel(schedulerActivation.scheduler_activation) },
        { label: "근거 생성 시각", value: schedulerActivation.generated_at || "미확인" },
        { label: "결과 위치", value: evidenceLocationLabel(data.scheduler.latest_artifact_root) },
        { label: "다음 조치", value: schedulerNextStepLabel(schedulerActivation) },
      ],
      title: schedulerReadinessTitle(data.scheduler),
    },
  };
}

function buildAutomationCardSources(
  data: DataHealthData,
  provider: string,
  runs: DataHealthPipelineRuns,
): readonly DataHealthAutomationCardSource[] {
  return [
    {
      description: "무료 가격 데이터 제공자의 한도를 확인한 뒤 일봉 캔들을 서버에 저장한다.",
      detail: `최근 가격 관측일 ${data.freshness.find((item) => item.dataset === "market.daily_price_bar")?.latest_observation_date ?? "미확인"} · 제공자 ${koCode(provider)}`,
      fallbackCadence: "일간 · 18:30",
      run: runs.marketPriceRun,
      title: "주식 캔들 수집",
    },
    {
      description: "저장소 밖 RSS 설정의 무료 뉴스 피드를 읽고 원문과 뉴스 이벤트로 저장한다.",
      detail: "뉴스는 이벤트, 종목 상세, 분석 지도, 추천 근거 점검으로 연결된다.",
      fallbackCadence: "일간 · 08:30",
      run: runs.newsRun,
      title: "뉴스 수집",
    },
    {
      description: "수집 문서를 구조화하고 AI 근거 기록을 남긴다. 중요 뉴스는 AI 배치 분석 후보로 처리하고, 뉴스 묶음은 무료 로컬 규칙 보조 증거로 남긴다.",
      detail: "AI는 근거를 정리하지만 매수·매도·주문 결론을 자동 실행하지 않는다.",
      fallbackCadence: "장중 · 2시간마다",
      run: runs.aiRun,
      title: "AI 분석",
    },
  ];
}

function buildNewsAfterAnalysisStepSources(
  runs: DataHealthPipelineRuns,
): readonly DataHealthNewsAfterAnalysisStepSource[] {
  return [
    {
      index: "01",
      next: "중복과 원천 링크를 남긴 뒤 이벤트 구조화 단계로 넘긴다.",
      output: "RSS/Atom 문서를 원문 저장소와 실행 기록에 저장한다.",
      owner: "news-rss-daily",
      run: runs.newsRun,
      title: "뉴스 원문 수집",
    },
    {
      index: "02",
      next: "동일 테마/종목 관계를 만들고 뉴스, 종목, 뉴스·AI 화면이 읽는다.",
      output: "헤드라인과 본문을 종목·테마·영향 방향이 있는 뉴스 이벤트로 정리한다.",
      owner: "news-rss-enrichment-intraday",
      run: runs.newsEnrichmentRun,
      title: "이벤트 구조화",
    },
    {
      index: "03",
      next: "검증을 통과한 근거만 표준 뉴스 영향으로 반영한다. 매수·매도·주문 결론은 여기서 만들지 않는다.",
      output: "중요 뉴스만 AI 배치 분석으로 처리해 종목·테마·방향·근거 항목을 AI 분석 기록에 남긴다.",
      owner: "event-intelligence-weekly",
      run: runs.aiRun,
      title: "AI 근거 생성",
    },
    {
      index: "04",
      next: "결정 로직은 재현 가능한 점수 계산이다. AI 근거는 설명 가능한 보조 근거로 붙는다.",
      output: "가격, 테마 연결, 이벤트 강도, 사이클 상태를 합쳐 추천 항목과 투자 논리 입력을 만든다.",
      owner: "decision-daily",
      run: runs.decisionRun,
      title: "신호와 추천 항목 갱신",
    },
    {
      index: "05",
      next: "추천 상세, 투자 논리, 보유 상태, 가상 매매 화면에서 본다.",
      output: "보유 투자 논리 유지 여부, 빈 가격/논리/성과 항목, 가상 거래 검증 문제를 큐로 만든다.",
      owner: "portfolio-remediation-daily",
      run: runs.remediationRun,
      title: "보유 상태와 운영 큐",
    },
  ];
}
