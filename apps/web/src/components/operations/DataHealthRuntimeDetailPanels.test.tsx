import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { DataHealthRuntimeDetailPanels } from "./DataHealthRuntimeDetailPanels";

describe("DataHealthRuntimeDetailPanels", () => {
  it("renders runtime details as Korean operator panels without raw internal codes", () => {
    render(
      <DataHealthRuntimeDetailPanels
        activeRecommendationPriceFreshness={{
          latestTradeDateLabel: "2026-06-24",
          nextActionLabel: "가격 보강 대기 없음",
          orderBoundaryLabel: "주문 차단",
          staleSummaryLabel: "오래됨 0개 · 없음 0개",
          staleSymbols: [
            {
              activeRecommendationCountLabel: "연결 추천 2개",
              daysBehindLabel: "최신 기준보다 1일 뒤처짐",
              href: "/stocks/NVDA",
              latestTradeDateLabel: "최근 가격 2026-06-23",
              statusLabel: "관찰",
              symbol: "NVDA",
            },
          ],
          statusLabel: "최신성 확인",
          statusTone: "risk-low",
          symbolCoverageLabel: "9/9개 최신",
        }}
        openGates={{
          chips: [{ key: "managed-wait", label: "성과 관찰 대기", tone: "risk-medium" }],
          freshnessRows: [{ datasetLabel: "뉴스 원장", valueLabel: "정상 · 2026-06-25" }],
          gates: [
            {
              id: "outcome-wait",
              label: "성과 표본 대기",
              nextActionLabel: "다음 측정일까지 대기",
              orderBoundaryLabel: "주문 차단",
              statusLabel: "관리 중",
              statusTone: "risk-medium",
              summary: "추천 산식 변경 전 표본이 성숙해야 한다.",
              typeLabel: "관리된 대기",
            },
          ],
        }}
        providerBudget={{
          budgetDateLabel: "2026-06-25",
          latestRunLabel: "2026-06-25 07:30",
          statusLabel: "정상",
          usagePercent: 31,
          usedRequestCountLabel: "250회",
        }}
        runtimeBoundary={{
          apiNextActionLabel: "추가 조치 없음",
          apiReadinessLabel: "운영 준비됨",
          artifactEvidenceLabel: "운영 증거 있음",
          artifactLatestRootLabel: "외부 보관 경로",
          artifactNextActionLabel: "추가 조치 없음",
          artifactPolicyLabel: "12/12개 · 최신 실행 12개",
          authNextActionLabel: "추가 조치 없음",
          authReadinessLabel: "읽기 전용 권한 준비",
          brokerOrderLabel: "쓰기 차단됨 · 주문 차단됨 · 읽기 전용",
          connectionLabel: "운영 · 실데이터 · DB 연결",
          environmentLabel: "준비됨",
          holidaySkipModeLabel: "휴장일 제외",
          notificationMethodLabel: "ntfy · 목적지 설정됨 · 테스트 통과",
          notificationNextActionLabel: "추가 조치 없음",
          notificationReadinessLabel: "외부 알림 검증됨",
          readProtectionLabel: "read-token · 읽기 토큰 설정됨 · 허용 출처 명시됨",
          readScopeLabel: "viewer · 보호된 화면 8개 · 읽기 요청만 허용",
          schedulerActivationAllowedLabel: "아니오",
          schedulerApprovalGateLabel: "승인 필요",
          schedulerEnvironmentLabel: "운영",
          schedulerJobLabel: "뉴스·가격·AI 분석",
          schedulerNextStepLabel: "자동 반복 실행 유지",
          schedulerReadinessLabel: "설치됨",
        }}
      />,
    );

    expect(screen.getByRole("heading", { name: "데이터 제공자 호출 예산" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "추천에 쓰는 가격이 최신인지 확인" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "조건과 데이터 최신성" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "반복 실행 준비 상태" })).toBeInTheDocument();
    expect(screen.getAllByText("주문 차단").length).toBeGreaterThan(1);
    expect(screen.queryByText(/broker_submit_allowed|read_only_no_order|pipeline-run/i)).not.toBeInTheDocument();
  });
});
