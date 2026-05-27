import Link from "next/link";
import type { Route } from "next";

export type ResearchFlowStepTone = "ready" | "watch" | "blocked" | "neutral";

export type ResearchFlowStep = {
  id: string;
  label: string;
  title: string;
  status: string;
  tone?: ResearchFlowStepTone;
  body: string;
  facts?: Array<{
    label: string;
    value: string;
  }>;
  href?: Route;
  hrefLabel?: string;
};

type ProfessionalResearchFlowProps = {
  eyebrow: string;
  title: string;
  summary: string;
  steps: ResearchFlowStep[];
  footer?: string;
};

export function ProfessionalResearchFlow({
  eyebrow,
  title,
  summary,
  steps,
  footer,
}: ProfessionalResearchFlowProps) {
  const readyCount = steps.filter((step) => step.tone === "ready").length;
  const watchCount = steps.filter((step) => step.tone === "watch" || step.tone === "neutral").length;
  const blockedCount = steps.filter((step) => step.tone === "blocked").length;

  return (
    <section className="research-flow reveal delay-1" aria-label={title}>
      <div className="research-flow-intro">
        <span className="metric-sub">{eyebrow}</span>
        <h2>{title}</h2>
        <p>{summary}</p>
        <div className="research-flow-summary" aria-label="전문 분석 흐름 요약">
          <div>
            <span>준비</span>
            <strong>{readyCount}</strong>
          </div>
          <div>
            <span>주의</span>
            <strong>{watchCount}</strong>
          </div>
          <div className={blockedCount > 0 ? "summary-blocked" : undefined}>
            <span>차단</span>
            <strong>{blockedCount}</strong>
          </div>
        </div>
        {blockedCount > 0 ? (
          <p className="research-flow-warning">
            차단 단계가 있으면 추천은 기록으로 남기되, 페이퍼 검증이나 주문 입력으로 넘기지 않는다.
          </p>
        ) : null}
        {footer ? <small>{footer}</small> : null}
      </div>

      <div className="research-flow-track">
        {steps.map((step) => (
          <article className={`research-flow-step tone-${step.tone ?? "neutral"}`} key={step.id}>
            <div className="research-flow-index">{step.label}</div>
            <div className="research-flow-copy">
              <div className="research-flow-step-heading">
                <strong>{step.title}</strong>
                <span>{step.status}</span>
              </div>
              <p>{step.body}</p>
              {step.facts && step.facts.length > 0 ? (
                <dl className="research-flow-facts">
                  {step.facts.map((fact) => (
                    <div key={`${step.id}-${fact.label}`}>
                      <dt>{fact.label}</dt>
                      <dd>{fact.value}</dd>
                    </div>
                  ))}
                </dl>
              ) : null}
              {step.href && step.hrefLabel ? (
                <Link className="research-flow-link" href={step.href}>
                  {step.hrefLabel}
                </Link>
              ) : null}
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
