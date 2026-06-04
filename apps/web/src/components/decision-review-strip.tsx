import Link from "next/link";
import type { Route } from "next";

export type DecisionReviewStep = {
  index: string;
  title: string;
  question: string;
  status: string;
  body: string;
  href: Route;
  cta: string;
  tone?: "ok" | "watch" | "block";
};

export function DecisionReviewStrip({
  eyebrow = "오늘 확인 순서",
  title = "수집에서 가상 매매 검증까지 같은 순서로 본다",
  description,
  activeIndex,
  steps,
}: {
  eyebrow?: string;
  title?: string;
  description?: string;
  activeIndex: string;
  steps: DecisionReviewStep[];
}) {
  return (
    <section className="decision-strip reveal delay-1" aria-labelledby="decision-strip-title">
      <div className="decision-strip-heading">
        <span>{eyebrow}</span>
        <h2 id="decision-strip-title">{title}</h2>
        {description ? <p>{description}</p> : null}
      </div>
      <div className="decision-strip-grid">
        {steps.map((step) => (
          <Link
            className={[
              "decision-strip-card",
              step.index === activeIndex ? "is-active" : "",
              step.tone ? `tone-${step.tone}` : "",
            ].filter(Boolean).join(" ")}
            href={step.href}
            key={`${step.index}-${step.href}`}
          >
            <span>{step.index}</span>
            <strong>{step.title}</strong>
            <em>{step.question}</em>
            <b>{step.status}</b>
            <p>{step.body}</p>
            <small>{step.cta}</small>
          </Link>
        ))}
      </div>
    </section>
  );
}
