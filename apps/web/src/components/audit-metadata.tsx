export type AuditMetadataItem = {
  label: string;
  value: string | number | boolean | null | undefined;
};

type AuditMetadataProps = {
  items: AuditMetadataItem[];
  summary?: string;
};

function formatAuditValue(value: AuditMetadataItem["value"]) {
  if (value === null || value === undefined || value === "") {
    return null;
  }
  if (typeof value !== "string") {
    return String(value);
  }

  const normalized = value.trim();
  if (!normalized || normalized.toLowerCase() === "null") {
    return null;
  }
  if (normalized.startsWith("pipeline-run-")) {
    const runNumber = normalized.replace("pipeline-run-", "").trim();
    return runNumber && runNumber.toLowerCase() !== "null"
      ? `실행 #${runNumber}`
      : "실행 번호 미연결";
  }
  return normalized;
}

export function AuditMetadata({ items, summary = "추적 메타데이터" }: AuditMetadataProps) {
  const visibleItems = items
    .map((item) => ({ ...item, value: formatAuditValue(item.value) }))
    .filter((item) => item.value !== null);

  if (visibleItems.length === 0) {
    return null;
  }

  return (
    <details className="audit-metadata">
      <summary>{summary}</summary>
      <dl>
        {visibleItems.map((item) => (
          <div key={`${item.label}-${item.value}`}>
            <dt>{item.label}</dt>
            <dd>{item.value}</dd>
          </div>
        ))}
      </dl>
    </details>
  );
}
