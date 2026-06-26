import type { LocalIngestWorker, ManualIngestSmoke, TossInvestMarketData } from "./dataHealthTypes";

import { koCode } from "@/lib/korean-labels";

export function manualSmokeTitle(smoke: ManualIngestSmoke) {
  if (smoke.status === "passed") {
    return "최근 수동 수집 성공";
  }
  if (smoke.status === "failed") {
    return "최근 수동 수집 중단";
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

export function manualSmokeExplanation(smoke: ManualIngestSmoke) {
  if (smoke.status === "passed") {
    return "가격, 뉴스, AI 분석 단발 작업이 실행됐고 중단된 작업이 없다는 뜻이다. 반복 자동화 상태는 별도로 본다.";
  }
  if (smoke.status === "failed") {
    return "단발 실행 중 중단된 작업이 있다. 실행 요약의 오류 내용과 작업 정보 확인이 필요합니다.";
  }
  if (smoke.status === "preview_not_executed") {
    return "실제 저장이나 외부 데이터 제공자 호출 없이 실행 계획만 생성한 상태다. 무료 API 한도를 쓰지 않고 어떤 작업이 돌지 확인한 것이다.";
  }
  if (smoke.status === "not_configured") {
    return "서버에 최근 수동 수집 결과 경로가 연결되지 않아 화면에서 읽을 수 없다.";
  }
  if (smoke.status === "missing_report") {
    return "환경변수는 설정됐지만 해당 요약 파일을 읽을 수 없다. 저장소 밖 경로에 요약 파일을 다시 생성해야 한다.";
  }
    return "수동 수집 상태를 확인하려면 결과 파일 형식과 생성 시각을 점검해야 한다.";
}

export function manualSmokeNextAction(smoke: ManualIngestSmoke) {
  return smoke.next_actions[0] ? koCode(smoke.next_actions[0]) : "다음 조치 없음";
}

export function localWorkerTitle(worker: LocalIngestWorker) {
  if (worker.status === "completed") {
    return "반복 실행 최근 성공";
  }
  if (worker.status === "failed") {
    return "반복 실행 최근 중단";
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

export function localWorkerExplanation(worker: LocalIngestWorker) {
  if (worker.status === "completed") {
    return "정해진 반복 실행 주기가 끝났고 중단된 주기가 없다는 뜻이다. 서버 예약 실행과 함께 자동 운영 상태를 판단한다.";
  }
  if (worker.status === "failed") {
    return "반복 실행 중 중단된 작업이 있었다. 최신 실행 요약과 오류 내용 확인이 필요합니다.";
  }
  if (worker.status === "preview_not_executed") {
    return "실제 저장이나 외부 데이터 제공자 호출 없이 반복 실행 계획만 확인한 상태다.";
  }
  if (worker.status === "not_configured") {
    return "서버에 반복 실행 결과 경로가 연결되지 않아 화면에서 읽을 수 없다.";
  }
  if (worker.status === "missing_report") {
    return "환경변수는 설정됐지만 반복 실행 결과 파일을 읽을 수 없다. 저장소 밖 경로에 결과를 다시 생성해야 한다.";
  }
  return "반복 실행 상태를 판단하려면 결과 파일 형식과 생성 시각을 점검해야 한다.";
}

export function localWorkerNextAction(worker: LocalIngestWorker) {
  return worker.next_actions[0] ? koCode(worker.next_actions[0]) : "다음 조치 없음";
}

export function tossMarketDataTitle(marketData: TossInvestMarketData) {
  if (marketData.sync.status === "succeeded") {
    return "토스증권 브로커 데이터 수집됨";
  }
  if (marketData.sync.status === "blocked_missing_credentials") {
    return "토스증권 API 키 필요";
  }
  if (marketData.sync.status === "missing") {
    return "토스증권 데이터 실행 이력 없음";
  }
  return koCode(marketData.sync.status);
}

export function tossMarketDataTone(marketData: TossInvestMarketData) {
  if (marketData.sync.attention_required) {
    return "risk-medium";
  }
  return "risk-low";
}
