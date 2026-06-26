import type { AuditSampleRecord, CycleAiQualityAudit } from "./dataHealthTypes";

import { koCode } from "@/lib/korean-labels";

import { isRecord } from "./dataHealthCopyModel";

export function qualityAuditTitle(audit: CycleAiQualityAudit) {
  if (audit.status === "ok") {
    return "품질 감사 통과";
  }
  if (audit.status === "degraded") {
    return "품질 감사 일부 부족";
  }
  if (audit.status === "managed_warning") {
    return "약한 전파 근거 관리 중";
  }
  if (audit.status === "attention_required") {
    return "오염 의심 항목 있음";
  }
  if (audit.status === "not_ready") {
    return "감사할 데이터 부족";
  }
  if (audit.status === "not_configured") {
    return "품질 감사 결과 미연결";
  }
  return koCode(audit.status);
}

export function qualityAuditExplanation(audit: CycleAiQualityAudit) {
  if (audit.status === "ok") {
    return "중복 뉴스, 잘못된 테마 연결, 원문 근거 없는 종목 연결, 약한 전파 근거가 현재 감사 기준에서 발견되지 않았다.";
  }
  if (audit.status === "degraded") {
    if (audit.readiness_gaps.length > 0) {
      return `큰 오염은 없지만 ${audit.readiness_gaps[0].label} 단계가 비어 있다. 이 단계가 채워져야 추천 근거 흐름을 끝까지 신뢰할 수 있다.`;
    }
    return "큰 오염은 없지만 번역, AI 분석, 전파, 사이클 스냅샷 중 일부 근거가 아직 부족하다.";
  }
  if (audit.status === "managed_warning") {
    return "치명적인 중복·오분류·근거 없는 직접 종목 연결은 없지만, 신뢰도나 경로 가중치가 낮은 전파 근거가 남아 있다. 사이클 스냅샷은 약한 전파를 제외하고 계산한다.";
  }
  if (audit.status === "attention_required") {
    return "추천 판단 전에 중복 뉴스, 종목 근거, 잘못된 테마 연결, 전파 근거가 약한 흐름 확인이 필요합니다.";
  }
  if (audit.status === "not_ready") {
    return "뉴스 수집부터 AI 분석, 전파, 사이클 스냅샷까지 한 번 더 실행한 뒤 판단해야 한다.";
  }
  if (audit.status === "not_configured") {
    return "서버에 최근 품질 감사 요약 파일 경로가 연결되지 않아 화면에서 읽을 수 없다.";
  }
  return "품질 감사 결과 파일의 상태와 생성 시각을 다시 확인해야 합니다.";
}

export function qualityAuditTone(audit: CycleAiQualityAudit) {
  if (audit.status === "ok") {
    return "risk-low";
  }
  if (audit.status === "degraded" || audit.status === "managed_warning" || audit.status === "not_configured") {
    return "risk-medium";
  }
  return "risk-high";
}

export function qualityMetric(audit: CycleAiQualityAudit, key: string) {
  const value = audit.metrics[key] ?? audit.checks[key] ?? 0;
  return typeof value === "number" ? value : Number(value || 0);
}

export function auditSampleRecords(audit: CycleAiQualityAudit, key: string) {
  const value = audit.samples[key];
  if (!Array.isArray(value)) {
    return [];
  }
  return value.filter(isRecord).slice(0, 5);
}

export function auditSampleValue(record: AuditSampleRecord, key: string) {
  const value = record[key];
  if (Array.isArray(value)) {
    return value
      .map((item) => auditSampleScalar(item))
      .filter(Boolean)
      .join(", ");
  }
  return auditSampleScalar(value);
}

export function auditSampleScalar(value: unknown) {
  if (typeof value === "string") {
    return value.trim();
  }
  if (typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  return "";
}

export function auditSampleHeadline(record: AuditSampleRecord) {
  const eventId = auditSampleValue(record, "event_id");
  return (
    auditSampleValue(record, "event_title")
    || auditSampleValue(record, "title")
    || (eventId ? `이벤트 ${eventId}` : "제목 미확인")
  );
}

export function auditSampleMeta(record: AuditSampleRecord) {
  const symbol = auditSampleValue(record, "symbol");
  const instrumentName = auditSampleValue(record, "instrument_name");
  const nodeCodes = auditSampleValue(record, "node_codes");
  const nodeCode = auditSampleValue(record, "node_code");
  const direction = auditSampleValue(record, "impact_direction")
    || auditSampleValue(record, "impact_directions");
  const repeatedCount = auditSampleValue(record, "repeated_count");
  const eventCount = auditSampleValue(record, "event_count");
  const documentCount = auditSampleValue(record, "document_count");
  const sourceNode = auditSampleValue(record, "source_node_code");
  const propagatedNode = auditSampleValue(record, "propagated_node_code");
  const confidence = auditSampleValue(record, "confidence");
  const pathWeight = auditSampleValue(record, "path_weight");
  return [
    symbol ? `종목 ${symbol}` : "",
    instrumentName ? instrumentName : "",
    nodeCodes ? `흐름 ${nodeCodes.split(", ").map(koCode).join(", ")}` : "",
    nodeCode ? `흐름 ${koCode(nodeCode)}` : "",
    sourceNode || propagatedNode
      ? `전파 ${sourceNode ? koCode(sourceNode) : "출발 미확인"} → ${propagatedNode ? koCode(propagatedNode) : "도착 미확인"}`
      : "",
    direction ? `방향 ${direction.split(", ").map(koCode).join(", ")}` : "",
    repeatedCount ? `반복 ${repeatedCount}회` : "",
    eventCount ? `이벤트 ${eventCount}개` : "",
    documentCount ? `문서 ${documentCount}개` : "",
    confidence ? `신뢰도 ${confidence}` : "",
    pathWeight ? `경로가중 ${pathWeight}` : "",
  ].filter(Boolean).join(" · ");
}

export function qualityAuditSampleGroups(audit: CycleAiQualityAudit) {
  return [
    {
      key: "duplicate_titles",
      label: "중복 뉴스",
      description: "같은 제목이 반복 수집되어 근거가 부풀려질 수 있는 후보.",
    },
    {
      key: "ungrounded_direct_tickers",
      label: "근거 없는 종목",
      description: "원문 제목·요약에서 종목 근거가 확인되지 않는 직접 연결 후보.",
    },
    {
      key: "macro_false_tickers",
      label: "거시 뉴스 종목 오부착",
      description: "거시 흐름으로 남겨야 하는 뉴스에 직접 종목이 붙은 후보.",
    },
    {
      key: "quantum_energy_mislinks",
      label: "테마 오분류",
      description: "양자컴퓨팅 뉴스가 에너지 흐름이나 XLE/XOM으로 잘못 연결된 후보.",
    },
    {
      key: "cross_theme_mismatches",
      label: "교차 테마 불일치",
      description: "뉴스 내용과 연결된 사이클 흐름이 강하게 어긋나는 후보.",
    },
    {
      key: "duplicate_flow_evidence",
      label: "중복 흐름 근거",
      description: "같은 뉴스가 여러 이벤트·흐름으로 분산되어 근거가 부풀려질 수 있는 후보.",
    },
    {
      key: "weak_propagation_evidence",
      label: "약한 전파 근거",
      description: "상위 흐름에서 종목으로 내려가는 경로의 신뢰도·강도·경로 가중치가 낮은 후보.",
    },
    {
      key: "normal_macro_flows",
      label: "정상 거시 흐름",
      description: "종목을 억지로 붙이지 않고 상위 흐름으로 처리한 정상 샘플.",
    },
  ].map((group) => ({
    ...group,
    records: auditSampleRecords(audit, group.key),
  })).filter((group) => group.records.length > 0);
}
