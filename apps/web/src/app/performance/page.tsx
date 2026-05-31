import Link from "next/link";
import type { Route } from "next";

import { getPerformanceOutcomes } from "@/lib/frontend-api";
import { koCode, koLabel } from "@/lib/korean-labels";
import type { PerformanceOutcomesData } from "@/lib/types";

export const dynamic = "force-dynamic";
export const metadata = { title: "성과 측정" };

function formatPercent(value: number) {
  return `${Math.round(value * 1000) / 10}%`;
}

function formatOptionalPercent(value: number | null) {
  return value === null ? "측정 대기" : formatPercent(value);
}

function formatBps(value: number) {
  const roundedPercentagePoint = Math.round((value / 100) * 100) / 100;
  return `${roundedPercentagePoint > 0 ? "+" : ""}${roundedPercentagePoint}%p`;
}

function recommendationHref(recommendationId: string) {
  return `/recommendations/${recommendationId}` as Route;
}

function thesisHref(thesisId: string) {
  return `/theses/${thesisId}` as Route;
}

function themeHref(themeKey: string | null) {
  return themeKey ? (`/themes/${themeKey}` as Route) : null;
}

function performanceCopy(value: string | null | undefined) {
  if (!value) {
    return "없음";
  }
  const directLabels: Record<string, string> = {
    component_lens_not_total_attribution: "관점별 해석이며 단순 합산값이 아니다",
    security_selection: "종목 선택",
    theme_exposure: "테마 노출",
    cash_timing: "현금 비중",
    coverage_ready: "커버리지 준비",
    outcome_run: "성과 측정 실행",
    methodology_boundary: "측정 방식 경계",
  };
  const labelled = directLabels[value] ?? koLabel(value);
  const base = labelled === value ? koCode(value) : labelled;
  return base
    .replaceAll("thesis", "투자 논리")
    .replaceAll("Thesis", "투자 논리")
    .replaceAll("outcome window", "성과 측정창")
    .replaceAll("outcome", "성과")
    .replaceAll("weight review", "추천 산식 검토")
    .replaceAll("weight", "가중치")
    .replaceAll("quality gate", "품질 기준")
    .replaceAll("gate", "기준")
    .replaceAll("coverage", "커버리지")
    .replaceAll("methodology", "측정 방식")
    .replaceAll("source run", "산출 실행")
    .replaceAll("source", "원천")
    .replaceAll("feedback", "사후평가")
    .replaceAll("calibration", "누적평가")
    .replaceAll("broker", "증권사")
    .replaceAll("paper validation", "페이퍼 검증");
}

function executionIdLabel(value: string) {
  if (value.startsWith("pipeline-run-")) {
    return `산출 실행 #${value.replace("pipeline-run-", "")}`;
  }
  return performanceCopy(value);
}

function gateColor(status: string) {
  if (status === "passed") {
    return "var(--accent-green)";
  }
  if (status === "blocked") {
    return "var(--accent-amber)";
  }
  return "var(--text-secondary)";
}

function evaluationStatusLabel(status: string) {
  const labels: Record<string, string> = {
    no_outcome_data: "성과 측정 전",
    insufficient_sample: "표본 부족",
    enough_sample: "표본 충분",
    needs_coverage_review: "커버리지 보완 필요",
    needs_quality_review: "품질 재검토 필요",
    positive_alignment: "성과 정렬 양호",
    reviewable: "검토 가능",
  };
  return labels[status] ?? koCode(status);
}

function evaluationStatusColor(status: string) {
  if (status === "positive_alignment") {
    return "var(--accent-green)";
  }
  if (status === "needs_quality_review") {
    return "var(--accent-red)";
  }
  if (status === "insufficient_sample" || status === "needs_coverage_review" || status === "no_outcome_data") {
    return "var(--accent-amber)";
  }
  return "var(--text-primary)";
}

function qualityCheckColor(status: string) {
  if (status === "passed") {
    return "var(--accent-green)";
  }
  if (status === "blocked") {
    return "var(--accent-red)";
  }
  return "var(--accent-amber)";
}

type AttributionComponent = PerformanceOutcomesData["attribution_components"][number];
type QualityGate = PerformanceOutcomesData["quality_gates"][number];

function attributionTitle(component: AttributionComponent) {
  if (component.component_type === "security_selection") {
    return component.symbol ? `${component.symbol} 종목 선택 효과` : "종목 선택 효과";
  }
  if (component.component_type === "theme_exposure") {
    return component.theme_key ? `${koCode(component.theme_key)} 테마 노출` : "테마 노출 효과";
  }
  if (component.component_type === "cash_timing") {
    return "현금 비중 효과";
  }
  return koLabel(component.label);
}

function attributionDescription(component: AttributionComponent) {
  if (component.component_type === "security_selection") {
    return `${component.symbol ?? "해당 종목"}의 벤치마크 대비 성과가 포트폴리오에 ${formatBps(component.contribution_bps)} 기여했다.`;
  }
  if (component.component_type === "theme_exposure") {
    return `관련 테마 묶음의 보유 비중 ${formatPercent(component.weight)}에서 ${formatBps(component.contribution_bps)} 기여가 발생했다.`;
  }
  if (component.component_type === "cash_timing") {
    return `현금 비중 ${formatPercent(component.weight)}은 이번 버전에서 별도 수익 기여 없이 리스크 완충 항목으로 추적한다.`;
  }
  return koLabel(component.interpretation);
}

function qualityGateReason(gate: QualityGate) {
  if (gate.gate === "coverage_ready") {
    return gate.status === "passed"
      ? "보유 종목에 투자 논리와 성과 측정 연결이 준비되어 있다."
      : "일부 보유 종목은 투자 논리나 성과 측정 연결이 부족해 성과 해석에서 제외된다.";
  }
  if (gate.gate === "outcome_run") {
    return gate.status === "passed"
      ? "이번 측정 구간에 추천 성과 결과가 존재한다."
      : "이번 측정 구간에 추천 성과 결과가 아직 없다.";
  }
  if (gate.gate === "methodology_boundary") {
    return "종목/테마 구성요소는 설명 관점이며 단순 합산 총액이 아니다.";
  }
  return performanceCopy(gate.reason);
}

export default async function PerformancePage() {
  const response = await getPerformanceOutcomes();
  const data = response.data;
  const quality = data.quality_evaluation;
  const hasMeasuredOutcomes = data.summary.measured_recommendation_count > 0 || data.outcomes.length > 0;
  const performanceCommandCards = [
    {
      index: "01",
      label: "측정 상태",
      title: hasMeasuredOutcomes ? `${data.summary.measured_recommendation_count}개 측정` : "성과 측정 전",
      metric: hasMeasuredOutcomes
        ? `평균 알파 ${formatPercent(data.summary.average_alpha)} · 적중률 ${formatPercent(data.summary.hit_rate)}`
        : `측정 종료 ${data.measurement_end_date}`,
      body: hasMeasuredOutcomes
        ? "측정 종료일이 지난 추천만 성과로 본다. 개별 추천과 투자 논리 링크를 열어 어떤 판단이 맞았는지 확인한다."
        : "아직 측정 가능한 추천 성과가 없다. 성과 측정창이 도래할 때까지 성과 해석과 추천 산식 검토를 보류한다.",
      href: "#performance-outcomes",
      cta: "성과 목록 보기",
      tone: hasMeasuredOutcomes ? "ready" : "watch",
    },
    {
      index: "02",
      label: "표본 품질",
      title: evaluationStatusLabel(quality.status),
      metric: `${quality.measured_recommendation_count}개 추천 · ${quality.measured_thesis_count}개 투자 논리`,
      body:
        quality.status === "positive_alignment"
          ? "성과 방향이 추천 점수와 대체로 맞는다. 그래도 표본 크기와 제외 항목을 같이 확인한다."
          : "성과 표본이 부족하거나 커버리지 보완이 필요하면 추천 산식 가중치를 바꾸면 안 된다.",
      href: "#performance-quality",
      cta: "품질 평가 보기",
      tone: quality.status === "positive_alignment" ? "ready" : "watch",
    },
    {
      index: "03",
      label: "귀속 해석",
      title:
        data.summary.attribution_component_count > 0
          ? `${data.summary.attribution_component_count}개 관점`
          : "귀속 관점 없음",
      metric: `종목 ${formatBps(data.summary.security_lens_contribution_bps)} · 테마 ${formatBps(data.summary.theme_lens_contribution_bps)}`,
      body:
        data.summary.attribution_component_count > 0
          ? "성과 귀속은 단순 합산 주문 근거가 아니라 종목·테마·현금 관점에서 왜 결과가 났는지 해석하는 자료다."
          : "성과 결과가 쌓이면 종목, 테마, 현금 관점의 해석이 생성된다.",
      href: "#performance-attribution",
      cta: "귀속 보기",
      tone: data.summary.attribution_component_count > 0 ? "ready" : "watch",
    },
    {
      index: "04",
      label: "제외·보완",
      title:
        data.summary.excluded_position_count > 0
          ? `${data.summary.excluded_position_count}개 제외`
          : "제외 없음",
      metric: `제외 비중 ${formatPercent(data.summary.excluded_weight)} · 현금 ${formatPercent(data.summary.cash_weight)}`,
      body:
        data.summary.excluded_position_count > 0
          ? "성과 해석에서 빠진 포지션이 있으면 먼저 투자 논리, 성과 측정, 원천 데이터를 보완해야 한다."
          : "현재 성과 귀속에서 제외된 포지션은 없다. 그래도 품질 기준은 계속 확인한다.",
      href: "#performance-exclusions",
      cta: "보완 항목 보기",
      tone: data.summary.excluded_position_count > 0 ? "block" : "ready",
    },
  ];

  return (
    <div className="pageStack">
      <section className="page-hero reveal" aria-labelledby="performance-title">
        <div className="bento-badge">
          성과 측정 • {koLabel(data.portfolio_name)} • {data.measurement_end_date}
        </div>
        <div>
          <h1 id="performance-title">성과를 확인하되, 아직 바꾸면 안 되는 것도 같이 본다.</h1>
          <p>
            이 화면은 장기 추천의 책임 추적 화면이다. 측정된 추천, 표본 품질, 성과 귀속,
            제외·보완 항목을 분리해서 보여주며 주문이나 추천 산식 가중치 변경을 실행하지 않는다.
          </p>
        </div>
      </section>

      <section className="performance-command-panel reveal delay-1" aria-labelledby="performance-command-title">
        <div className="performance-command-lead">
          <span>성과 판정판</span>
          <h2 id="performance-command-title">결과가 좋아 보이는지보다, 믿고 써도 되는지 먼저 본다.</h2>
          <p>
            측정 구간 {data.measurement_start_date} ~ {data.measurement_end_date} · 벤치마크 {data.benchmark_code}.
            성과는 추천 품질 검증 자료이고, 자동 주문·자동 추천 산식 변경 근거가 아니다.
          </p>
        </div>
        <div className="performance-command-grid">
          {performanceCommandCards.map((card) => (
            <a className={`performance-command-card ${card.tone}`} href={card.href} key={card.index}>
              <span>{card.index}</span>
              <small>{card.label}</small>
              <strong>{card.title}</strong>
              <em>{card.metric}</em>
              <p>{card.body}</p>
              <b>{card.cta}</b>
            </a>
          ))}
        </div>
      </section>

      <section className="bento-grid reveal delay-1" aria-label="성과 핵심 요약">
        <article className="bento-card">
          <span className="metric-label">적중률</span>
          <strong className="metric-value">{hasMeasuredOutcomes ? formatPercent(data.summary.hit_rate) : "측정 전"}</strong>
          <span className="metric-sub">
            {hasMeasuredOutcomes
              ? `상회 ${data.summary.outperform_count} / 하회 ${data.summary.underperform_count}`
              : "측정 종료일이 지난 추천부터 집계"}
          </span>
        </article>
        <article className="bento-card">
          <span className="metric-label">측정된 투자 논리</span>
          <strong className="metric-value">{data.summary.measured_thesis_count}</strong>
          <span className="metric-sub">추천 {data.summary.measured_recommendation_count}개</span>
        </article>
        <article className="bento-card">
          <span className="metric-label">종목 관점</span>
          <strong className="metric-value">
            {hasMeasuredOutcomes ? formatBps(data.summary.security_lens_contribution_bps) : "측정 전"}
          </strong>
          <span className="metric-sub">{performanceCopy(data.methodology)}</span>
        </article>
        <article className="bento-card" style={{ borderColor: data.summary.excluded_position_count > 0 ? "rgba(245, 158, 11, 0.45)" : "var(--border-light)" }}>
          <span className="metric-label">제외 비중</span>
          <strong className="metric-value" style={{ color: data.summary.excluded_position_count > 0 ? "var(--accent-amber)" : "var(--text-primary)" }}>
            {formatPercent(data.summary.excluded_weight)}
          </strong>
          <span className="metric-sub">{data.summary.excluded_position_count}개 포지션 커버리지 필요</span>
        </article>
      </section>

      <section className="bento-grid reveal delay-2">
        <article id="performance-quality" className="bento-card span-4" style={{ borderColor: evaluationStatusColor(quality.status) }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "16px", flexWrap: "wrap", marginBottom: "20px" }}>
            <div>
              <span className="metric-sub">추천 품질 평가</span>
              <h2 style={{ fontSize: "1.5rem", marginTop: "6px" }}>{evaluationStatusLabel(quality.status)}</h2>
              <p style={{ color: "var(--text-secondary)", marginTop: "8px", maxWidth: "720px" }}>
                이 평가는 추천을 새로 만들지 않는다. 이미 저장된 추천 점수, 성과, 보유 검토, 커버리지를 대조해
                중장기 추천 품질을 과대 해석하지 않도록 점검한다.
              </p>
            </div>
            <div style={{ textAlign: "right", minWidth: "180px" }}>
              <span className="metric-sub">평균 알파</span>
              <strong style={{ display: "block", fontSize: "2rem", color: evaluationStatusColor(quality.status) }}>
                {formatOptionalPercent(quality.average_alpha)}
              </strong>
              <span className="metric-sub">적중률 {formatOptionalPercent(quality.hit_rate)}</span>
            </div>
          </div>

          <div className="bento-grid" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", marginBottom: "18px" }}>
            <div>
              <span className="metric-label">측정 추천</span>
              <strong className="metric-value">{quality.measured_recommendation_count}</strong>
              <span className="metric-sub">{evaluationStatusLabel(quality.sample_size_status)}</span>
            </div>
            <div>
              <span className="metric-label">고점수 추천</span>
              <strong className="metric-value">{quality.high_score_recommendation_count}</strong>
              <span className="metric-sub">평균 알파 {formatOptionalPercent(quality.high_score_average_alpha)}</span>
            </div>
            <div>
              <span className="metric-label">검토-성과 충돌</span>
              <strong className="metric-value">{quality.review_outcome_mismatch_count}</strong>
              <span className="metric-sub">보유 판단과 결과 대조</span>
            </div>
            <div>
              <span className="metric-label">커버리지 제외</span>
              <strong className="metric-value">{quality.coverage_exclusion_count}</strong>
              <span className="metric-sub">먼저 보완할 빈칸</span>
            </div>
          </div>

          <div className="bento-list">
            {quality.checks.length === 0 ? (
              <p className="empty-state">아직 성과 검토 기준이 실행되지 않았다. 성과 측정이 생성되면 여기에 확인 항목이 표시된다.</p>
            ) : null}
            {quality.checks.map((check) => (
              <div className="bento-list-item" key={check.check_key} style={{ alignItems: "flex-start" }}>
                <div>
                  <strong>{performanceCopy(check.label)}</strong>
                  <span>{performanceCopy(check.detail)}</span>
                  <span>{performanceCopy(check.next_step)}</span>
                </div>
                <strong style={{ color: qualityCheckColor(check.status) }}>
                  {koCode(check.status)}
                </strong>
              </div>
            ))}
          </div>
        </article>

        <article id="performance-outcomes" className="bento-card span-4">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: "24px", gap: "16px", flexWrap: "wrap" }}>
            <div>
              <span className="metric-sub">측정된 성과</span>
              <h2 style={{ fontSize: "1.5rem" }}>추천 책임 추적</h2>
            </div>
            <Link className="btn btn-secondary" href="/portfolio/coverage">
              커버리지 확인 열기
            </Link>
          </div>
          <div className="bento-list">
            {data.outcomes.length === 0 ? (
              <p className="empty-state">
                아직 측정 종료일이 지난 추천 성과가 없다. 성과 측정 윈도우가 도래하면 추천별 알파와
                벤치마크 대비 결과가 이 영역에 표시된다.
              </p>
            ) : null}
            {data.outcomes.map((outcome) => (
              <div className="bento-list-item" key={outcome.outcome_id} style={{ alignItems: "flex-start" }}>
                <div style={{ flex: 1 }}>
                  <span className="metric-sub">
                    {outcome.symbol} • {outcome.horizon_days}일 • {data.measurement_start_date} ~ {data.measurement_end_date}
                  </span>
                  <strong style={{ fontSize: "1.05rem" }}>{koCode(outcome.recommendation)} / {koCode(outcome.label)}</strong>
                  <span>{executionIdLabel(outcome.source_run_id)}</span>
                  <div style={{ display: "flex", gap: "10px", flexWrap: "wrap", marginTop: "8px" }}>
                    <Link className="btn btn-secondary" href={recommendationHref(outcome.recommendation_id)}>
                      추천
                    </Link>
                    <Link className="btn btn-secondary" href={thesisHref(outcome.thesis_id)}>
                      투자 논리
                    </Link>
                  </div>
                </div>
                <div style={{ alignItems: "flex-end", minWidth: "220px" }}>
                  <strong style={{ color: outcome.alpha >= 0 ? "var(--accent-green)" : "var(--accent-red)", fontSize: "1.25rem" }}>
                    알파 {formatPercent(outcome.alpha)}
                  </strong>
                  <span>절대수익률 {formatPercent(outcome.absolute_return)}</span>
                  <span>벤치마크 {formatPercent(outcome.benchmark_return)}</span>
                  <span>기여도 {formatBps(outcome.security_contribution_bps)}</span>
                </div>
              </div>
            ))}
          </div>
        </article>

        <article id="performance-attribution" className="bento-card span-2">
          <div style={{ marginBottom: "24px" }}>
            <span className="metric-sub">성과 해석 관점</span>
            <h2 style={{ fontSize: "1.5rem" }}>합산값이 아니라 해석 관점</h2>
          </div>
          <div className="bento-list">
            {data.attribution_components.length === 0 ? (
              <p className="empty-state">성과 결과가 없어서 아직 귀속 관점이 생성되지 않았다.</p>
            ) : null}
            {data.attribution_components.map((component) => {
              const href = themeHref(component.theme_key);
              return (
                <div className="bento-list-item" key={component.component_id} style={{ alignItems: "flex-start" }}>
                  <div style={{ flex: 1 }}>
                    <span className="metric-sub">{performanceCopy(component.component_type)}</span>
                    <strong>{attributionTitle(component)}</strong>
                    <span>{attributionDescription(component)}</span>
                    {href ? (
                      <Link href={href} style={{ color: "var(--accent-blue)", fontSize: "0.75rem", textDecoration: "underline", textUnderlineOffset: "3px", marginTop: "4px" }}>
                        테마 열기
                      </Link>
                    ) : null}
                  </div>
                  <div style={{ alignItems: "flex-end", minWidth: "92px" }}>
                    <strong style={{ color: component.contribution_bps > 0 ? "var(--accent-green)" : "var(--text-primary)" }}>
                      {formatBps(component.contribution_bps)}
                    </strong>
                    <span>비중 {formatPercent(component.weight)}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </article>

        <article id="performance-exclusions" className="bento-card span-2">
          <div style={{ marginBottom: "24px" }}>
            <span className="metric-sub">커버리지 제외</span>
            <h2 style={{ fontSize: "1.5rem" }}>커버리지 부족 항목</h2>
          </div>
          <div className="bento-list">
            {data.coverage_exclusions.length === 0 ? (
              <p className="empty-state">성과 귀속에서 제외된 포지션이 없다.</p>
            ) : null}
            {data.coverage_exclusions.map((exclusion) => (
              <div className="bento-list-item" key={exclusion.instrument_id}>
                <div>
                  <strong>{exclusion.symbol}</strong>
                  <span>{performanceCopy(exclusion.reason)}</span>
                </div>
                <div style={{ alignItems: "flex-end" }}>
                  <strong style={{ color: "var(--accent-amber)" }}>{formatPercent(exclusion.weight)}</strong>
                  <span>{performanceCopy(exclusion.required_action)}</span>
                </div>
              </div>
            ))}
          </div>
          <div className="btn-row">
            <Link className="btn btn-secondary" href="/remediation">
              보완 큐 열기
            </Link>
          </div>
        </article>

        <article className="bento-card span-4">
          <div style={{ marginBottom: "24px" }}>
            <span className="metric-sub">성과 검토 기준</span>
            <h2 style={{ fontSize: "1.5rem" }}>성과를 과대 해석하지 않기</h2>
          </div>
          <div className="bento-list">
            {data.quality_gates.map((gate) => (
              <div className="bento-list-item" key={gate.gate}>
                <div>
                  <strong>{performanceCopy(gate.gate)}</strong>
                  <span>{qualityGateReason(gate)}</span>
                </div>
                <strong style={{ color: gateColor(gate.status), textTransform: "uppercase" }}>{koCode(gate.status)}</strong>
              </div>
            ))}
          </div>
        </article>
      </section>
    </div>
  );
}
