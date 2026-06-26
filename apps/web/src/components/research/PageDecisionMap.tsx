import styles from "./PageDecisionMap.module.css";

export type DecisionMapTone = "ready" | "watch" | "block";

export type DecisionMapStep = {
  readonly href: string;
  readonly label: string;
  readonly title: string;
  readonly description: string;
  readonly status: string;
  readonly tone: DecisionMapTone;
};

export type PageDecisionMapProps = {
  readonly eyebrow: string;
  readonly title: string;
  readonly description: string;
  readonly steps: readonly DecisionMapStep[];
  readonly density?: "comfortable" | "compact";
};

const toneClassName: Record<DecisionMapTone, string> = {
  block: styles.block,
  ready: styles.ready,
  watch: styles.watch,
};

export function PageDecisionMap({ eyebrow, title, description, steps, density = "comfortable" }: PageDecisionMapProps) {
  return (
    <section className={`${styles.map} ${density === "compact" ? styles.compact : ""}`} aria-label={title}>
      <div className={styles.copy}>
        <span>{eyebrow}</span>
        <h2>{title}</h2>
        <p>{description}</p>
      </div>
      <ol className={styles.steps} aria-label="화면 확인 순서">
        {steps.map((step, index) => (
          <li className={styles.step} key={step.href}>
            <a href={step.href}>
              <span>{String(index + 1).padStart(2, "0")}</span>
              <em>{step.label}</em>
              <strong>{step.title}</strong>
              <small>{step.description}</small>
              <b className={toneClassName[step.tone]}>{step.status}</b>
            </a>
          </li>
        ))}
      </ol>
    </section>
  );
}
