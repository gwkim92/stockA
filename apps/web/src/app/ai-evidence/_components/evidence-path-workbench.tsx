import Link from "next/link";
import type { Route } from "next";

export type EvidencePathTone = "ready" | "watch" | "blocked";

export type EvidencePathStep = {
  index: string;
  label: string;
  value: string;
  body: string;
  tone?: EvidencePathTone;
  href?: Route | `#${string}` | null;
  cta?: string;
};

type EvidencePathWorkbenchProps = {
  eyebrow: string;
  title: string;
  summary: string;
  verdict: string;
  verdictTone?: EvidencePathTone;
  steps: EvidencePathStep[];
};

function toneClass(tone: EvidencePathTone | undefined) {
  if (tone === "blocked") {
    return "is-blocked";
  }
  if (tone === "watch") {
    return "is-watch";
  }
  return "is-ready";
}

function EvidencePathAction({ href, cta }: Pick<EvidencePathStep, "href" | "cta">) {
  if (!href || !cta) {
    return null;
  }
  if (href.startsWith("#")) {
    return <a href={href}>{cta}</a>;
  }
  return <Link href={href}>{cta}</Link>;
}

export function EvidencePathWorkbench({
  eyebrow,
  title,
  summary,
  verdict,
  verdictTone = "watch",
  steps,
}: EvidencePathWorkbenchProps) {
  return (
    <section className={`evidence-path-workbench ${toneClass(verdictTone)} reveal delay-1`} aria-labelledby="evidence-path-workbench-title">
      <div className="evidence-path-workbench-copy">
        <span>{eyebrow}</span>
        <h2 id="evidence-path-workbench-title">{title}</h2>
        <p>{summary}</p>
        <strong>{verdict}</strong>
      </div>
      <ol className="evidence-path-workbench-steps" aria-label="투자 근거 판단 경로">
        {steps.map((step) => (
          <li className={toneClass(step.tone)} key={`${step.index}-${step.label}`}>
            <span>{step.index}</span>
            <strong>{step.label}</strong>
            <em>{step.value}</em>
            <p>{step.body}</p>
            <EvidencePathAction href={step.href} cta={step.cta} />
          </li>
        ))}
      </ol>
    </section>
  );
}
