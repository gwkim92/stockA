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
    coverage_ready: "성과 연결 준비",
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
    .replaceAll("weight review", "추천 산식 변경 여부")
    .replaceAll("weight", "추천 산식 반영 비중")
    .replaceAll("quality gate", "품질 기준")
    .replaceAll("gate", "기준")
    .replaceAll("coverage", "성과 연결 상태")
    .replaceAll("methodology", "측정 방식")
    .replaceAll("source run", "산출 실행")
    .replaceAll("source", "원천")
    .replaceAll("feedback", "사후평가")
    .replaceAll("calibration", "누적평가")
    .replaceAll("broker", "증권사 연결")
    .replaceAll("paper validation", "가상 매매 검증")
    .replaceAll("커버리지", "연결 상태")
    .replaceAll("가중치", "반영 비중")
    .replaceAll(["페", "이퍼"].join(""), "가상 매매");
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
    needs_coverage_review: "성과 연결 보완 필요",
    needs_quality_review: "품질 재확인 필요",
    positive_alignment: "성과 정렬 양호",
    reviewable: "확인 가능",
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

function statusToneClass(status: string) {
  if (status === "passed" || status === "positive_alignment" || status === "reviewable") {
    return "is-good";
  }
  if (status === "blocked" || status === "needs_quality_review") {
    return "is-block";
  }
  return "is-watch";
}

function alphaToneClass(value: number | null) {
  if (value === null) {
    return "is-watch";
  }
  return value >= 0 ? "is-good" : "is-block";
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
        ? "측정 종료일이 지난 추천만 성과로 본다. 개별 추천과 투자 논리 링크를 열어 어떤 근거가 성과와 맞았는지 확인한다."
        : "아직 측정 가능한 추천 성과가 없다. 성과 측정창이 도래할 때까지 성과 해석과 추천 산식 변경을 보류한다.",
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
          : "성과 표본이 부족하거나 성과 연결 보완이 필요하면 추천 산식 반영 비중을 바꾸면 안 된다.",
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
    <div className="pageStack decision-page">
      <section className="decision-brief reveal" aria-labelledby="performance-title">
        <div className="decision-brief-main">
          <span className="decision-brief-kicker">
            성과 측정 · {koLabel(data.portfolio_name)} · {data.measurement_end_date}
          </span>
          <h1 className="decision-brief-title" id="performance-title">
            성과 표본은 아직 산식 변경 근거가 아니다.
          </h1>
          <p className="decision-brief-copy">
            측정된 추천, 표본 품질, 성과 귀속, 제외·보완 항목을 분리해서 본다. 표본이 부족하면 추천 산식과 주문 판단은 그대로 잠근다.
          </p>
          <div className="decision-brief-meta" aria-label="성과 핵심 상태">
            <span>측정 구간 {data.measurement_start_date} ~ {data.measurement_end_date}</span>
            <span>벤치마크 {data.benchmark_code}</span>
            <span>적중률 {hasMeasuredOutcomes ? formatPercent(data.summary.hit_rate) : "측정 전"}</span>
            <span>제외 {data.summary.excluded_position_count.toLocaleString("ko-KR")}개</span>
          </div>
        </div>
        <div className="decision-brief-grid">
          {performanceCommandCards.map((card) => (
            <a
              className={`decision-card ${
                card.tone === "ready" ? "is-good" : card.tone === "watch" ? "is-watch" : "is-block"
              }`}
              href={card.href}
              key={card.index}
            >
              <span>{card.label}</span>
              <strong>{card.title}</strong>
              <small>{card.metric} · {card.body}</small>
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
          <span className="metric-sub">{data.summary.excluded_position_count}개 포지션 연결 상태 보완 필요</span>
        </article>
      </section>

      <section className="performance-workbench reveal delay-2" aria-label="성과 상세 점검">
        <article id="performance-quality" className={`performance-panel performance-panel-wide ${statusToneClass(quality.status)}`}>
          <div className="performance-panel-head">
            <div>
              <span>추천 품질 평가</span>
              <h2>{evaluationStatusLabel(quality.status)}</h2>
              <p>
                이 평가는 추천을 새로 만들지 않는다. 이미 저장된 추천 점수, 성과, 보유 상태, 성과 연결 상태를
                대조해 중장기 추천 품질을 과대 해석하지 않도록 점검한다.
              </p>
            </div>
            <div className={`performance-status-badge ${alphaToneClass(quality.average_alpha)}`}>
              <span>평균 알파</span>
              <strong>{formatOptionalPercent(quality.average_alpha)}</strong>
              <small>적중률 {formatOptionalPercent(quality.hit_rate)}</small>
            </div>
          </div>

          <div className="performance-metric-grid">
            <div>
              <span>측정 추천</span>
              <strong>{quality.measured_recommendation_count}</strong>
              <small>{evaluationStatusLabel(quality.sample_size_status)}</small>
            </div>
            <div>
              <span>고점수 추천</span>
              <strong>{quality.high_score_recommendation_count}</strong>
              <small>평균 알파 {formatOptionalPercent(quality.high_score_average_alpha)}</small>
            </div>
            <div>
              <span>보유 상태-성과 충돌</span>
              <strong>{quality.review_outcome_mismatch_count}</strong>
              <small>보유 상태와 결과 대조</small>
            </div>
            <div>
              <span>성과 연결 제외</span>
              <strong>{quality.coverage_exclusion_count}</strong>
              <small>먼저 보완할 빈칸</small>
            </div>
          </div>

          <div className="performance-check-grid">
            {quality.checks.length === 0 ? (
              <p className="empty-state">아직 성과 해석 기준이 실행되지 않았다. 성과 측정이 생성되면 여기에 확인 항목이 표시된다.</p>
            ) : null}
            {quality.checks.map((check) => (
              <article className={`performance-check-card ${statusToneClass(check.status)}`} key={check.check_key}>
                <div>
                  <strong>{performanceCopy(check.label)}</strong>
                  <span>{performanceCopy(check.detail)}</span>
                  <span>{performanceCopy(check.next_step)}</span>
                </div>
                <b style={{ color: qualityCheckColor(check.status) }}>{koCode(check.status)}</b>
              </article>
            ))}
          </div>
        </article>

        <article id="performance-outcomes" className="performance-panel performance-panel-wide">
          <div className="performance-panel-head compact">
            <div>
              <span>측정된 성과</span>
              <h2>추천 책임 추적</h2>
              <p>추천이 실제로 벤치마크를 이겼는지와 어떤 투자 논리로 연결되는지 확인한다.</p>
            </div>
            <Link className="btn btn-secondary" href="/portfolio/coverage">
              보유·리스크 상태 열기
            </Link>
          </div>
          <div className="performance-outcome-grid">
            {data.outcomes.length === 0 ? (
              <p className="empty-state">
                아직 측정 종료일이 지난 추천 성과가 없다. 성과 측정 윈도우가 도래하면 추천별 알파와
                벤치마크 대비 결과가 이 영역에 표시된다.
              </p>
            ) : null}
            {data.outcomes.map((outcome) => (
              <article className={`performance-outcome-card ${alphaToneClass(outcome.alpha)}`} key={outcome.outcome_id}>
                <div className="performance-outcome-main">
                  <span>
                    {outcome.symbol} • {outcome.horizon_days}일 • {data.measurement_start_date} ~ {data.measurement_end_date}
                  </span>
                  <strong>{koCode(outcome.recommendation)} / {koCode(outcome.label)}</strong>
                  <small>{executionIdLabel(outcome.source_run_id)}</small>
                  <div className="performance-card-links">
                    <Link className="btn btn-secondary" href={recommendationHref(outcome.recommendation_id)}>
                      추천 보기
                    </Link>
                    <Link className="btn btn-secondary" href={thesisHref(outcome.thesis_id)}>
                      투자 논리 보기
                    </Link>
                  </div>
                </div>
                <div className="performance-return-stack">
                  <strong>알파 {formatPercent(outcome.alpha)}</strong>
                  <span>절대수익률 {formatPercent(outcome.absolute_return)}</span>
                  <span>벤치마크 {formatPercent(outcome.benchmark_return)}</span>
                  <span>기여도 {formatBps(outcome.security_contribution_bps)}</span>
                </div>
              </article>
            ))}
          </div>
        </article>

        <article id="performance-attribution" className="performance-panel">
          <div className="performance-panel-head compact">
            <div>
              <span>성과 해석 관점</span>
              <h2>합산값이 아니라 해석 관점</h2>
              <p>종목·테마·현금이 결과를 어떻게 설명하는지 나눠 본다.</p>
            </div>
          </div>
          <div className="performance-mini-card-grid">
            {data.attribution_components.length === 0 ? (
              <p className="empty-state">성과 결과가 없어서 아직 귀속 관점이 생성되지 않았다.</p>
            ) : null}
            {data.attribution_components.map((component) => {
              const href = themeHref(component.theme_key);
              return (
                <article className={`performance-mini-card ${alphaToneClass(component.contribution_bps)}`} key={component.component_id}>
                  <div>
                    <span>{performanceCopy(component.component_type)}</span>
                    <strong>{attributionTitle(component)}</strong>
                    <small>{attributionDescription(component)}</small>
                    {href ? (
                      <Link href={href}>
                        테마 열기
                      </Link>
                    ) : null}
                  </div>
                  <b>{formatBps(component.contribution_bps)}</b>
                  <em>비중 {formatPercent(component.weight)}</em>
                </article>
              );
            })}
          </div>
        </article>

        <article id="performance-exclusions" className="performance-panel">
          <div className="performance-panel-head compact">
            <div>
              <span>성과 연결 제외</span>
              <h2>성과 연결 보완 항목</h2>
              <p>성과 해석에서 빠진 포지션이 있으면 추천 평가보다 원천 연결을 먼저 보완한다.</p>
            </div>
          </div>
          <div className="performance-mini-card-grid">
            {data.coverage_exclusions.length === 0 ? (
              <p className="empty-state">성과 귀속에서 제외된 포지션이 없다.</p>
            ) : null}
            {data.coverage_exclusions.map((exclusion) => (
              <article className="performance-mini-card is-watch" key={exclusion.instrument_id}>
                <div>
                  <span>보완 대상</span>
                  <strong>{exclusion.symbol}</strong>
                  <small>{performanceCopy(exclusion.reason)}</small>
                </div>
                <b>{formatPercent(exclusion.weight)}</b>
                <em>{performanceCopy(exclusion.required_action)}</em>
              </article>
            ))}
          </div>
          <div className="performance-card-links">
            <Link className="btn btn-secondary" href="/remediation">
              보완 큐 열기
            </Link>
          </div>
        </article>

        <article className="performance-panel performance-panel-wide">
          <div className="performance-panel-head compact">
            <div>
              <span>성과 해석 기준</span>
              <h2>성과를 과대 해석하지 않기</h2>
              <p>성과가 있어도 표본, 원천 연결, 측정 방식 경계가 부족하면 추천 산식 반영 비중은 바꾸지 않는다.</p>
            </div>
          </div>
          <div className="performance-gate-grid">
            {data.quality_gates.map((gate) => (
              <article className={`performance-gate-card ${statusToneClass(gate.status)}`} key={gate.gate}>
                <div>
                  <span>{performanceCopy(gate.gate)}</span>
                  <strong>{qualityGateReason(gate)}</strong>
                </div>
                <b>{koCode(gate.status)}</b>
              </article>
            ))}
          </div>
        </article>
      </section>
    </div>
  );
}
