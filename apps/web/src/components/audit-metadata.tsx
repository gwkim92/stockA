export type AuditMetadataItem = {
  label: string;
  value: string | number | boolean | null | undefined;
};

type AuditMetadataProps = {
  items: AuditMetadataItem[];
  summary?: string;
};

export function AuditMetadata({ items, summary = "추적 메타데이터" }: AuditMetadataProps) {
  const visibleItems = items.filter((item) => item.value !== null && item.value !== undefined && item.value !== "");

  if (visibleItems.length === 0) {
    return null;
  }

  return (
    <details className="audit-metadata">
      <summary>{summary}</summary>
      <dl>
        {visibleItems.map((item) => (
          <div key={`${item.label}-${String(item.value)}`}>
            <dt>{item.label}</dt>
            <dd>{String(item.value)}</dd>
          </div>
        ))}
      </dl>
    </details>
  );
}
