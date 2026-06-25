import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { DataHealthAutomationDetailSection } from "./DataHealthAutomationDetailSection";
import { DataHealthExecutionHistoryPanel } from "./DataHealthExecutionHistoryPanel";

describe("DataHealthExecutionHistoryPanel", () => {
  it("renders execution history with Korean labels and without raw internal status codes", () => {
    render(
      <DataHealthExecutionHistoryPanel
        rows={[
          {
            domainLabel: "뉴스·AI",
            finishedAtLabel: "2026-06-25T08:30:00Z",
            id: "pipeline-run-101",
            latestRunLabel: "실행 101",
            pipelineNameLabel: "뉴스 수집",
            cadenceLabel: "장중 반복",
            statusLabel: "성공",
            statusTone: "risk-low",
            freshnessLabel: "정상",
          },
        ]}
      />,
    );

    expect(screen.getByRole("heading", { name: "작업 실행 이력" })).toBeInTheDocument();
    expect(screen.getByText("뉴스 수집")).toBeInTheDocument();
    expect(screen.getByText("장중 반복")).toBeInTheDocument();
    expect(screen.queryByText(/read_only_no_order|broker_submit_allowed/i)).not.toBeInTheDocument();
  });
});

describe("DataHealthAutomationDetailSection", () => {
  it("renders scheduler details as an operator-only disclosure", () => {
    render(
      <DataHealthAutomationDetailSection
        automationStatusLabel="반복 실행 중"
        automationCards={[
          {
            cadenceLabel: "일간 · 18:30",
            description: "일봉 캔들을 서버에 저장한다.",
            detail: "최근 가격 관측일 2026-06-24",
            finishedAtLabel: "2026-06-25T08:30:00Z",
            stateLabel: "최근 실행 성공",
            title: "주식 캔들 수집",
          },
        ]}
        localWorker={{
          description: "현재 서버 자동화의 주 근거가 아니다.",
          factRows: [{ label: "상태", value: "완료" }],
          title: "현재 서버 자동화의 주 근거가 아니다",
          eyebrow: "과거 로컬 워커 기록",
          cycleRows: [],
        }}
        manualSmoke={{
          description: "자동 운영 전 수동 검증 기록이다.",
          factRows: [{ label: "상태", value: "통과" }],
          title: "자동 운영 전 수동 검증 기록",
          eyebrow: "과거 수동 점검 증거",
          artifactRows: [],
        }}
        newsAfterAnalysisSteps={[
          {
            finishedAtLabel: "2026-06-25T08:30:00Z",
            index: "01",
            next: "이벤트 구조화 단계로 넘긴다.",
            output: "RSS 문서를 저장한다.",
            ownerLabel: "뉴스 수집",
            statusLabel: "최근 실행 성공",
            title: "뉴스 원문 수집",
            warningLabel: "",
          },
        ]}
        profileScheduler={{
          activeTimerSummaryLabel: "7/7개 예약 실행 활성",
          timers: [
            {
              activeStateLabel: "활성",
              lastResultLabel: "성공",
              nextElapseLabel: "내일 08:30",
              profileLabel: "뉴스·AI 분석",
              scheduleLabel: "매 30분",
            },
          ],
        }}
        schedulerDetail={{
          description: "서버 예약 실행기가 데이터 수집과 분석 작업을 주기별로 호출한다.",
          factRows: [
            { label: "승인 조건", value: "서버 반복 실행 설치 완료" },
            { label: "다음 조치", value: "자동 반복 실행 유지" },
          ],
          title: "서버 반복 실행기 작동 중",
        }}
      />,
    );

    expect(screen.getByText("상세 운영 기록")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "서버 반복 실행기 작동 중" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "웹 화면은 저장된 결과를 읽고, 서버 예약 작업이 수집·분석을 실행한다" })).toBeInTheDocument();
    expect(screen.getByText("뉴스 원문 수집")).toBeInTheDocument();
    expect(screen.queryByText(/runner|artifact|pipeline-run/i)).not.toBeInTheDocument();
  });
});
