export function formatCount(value: number | null | undefined, unit = "건"): string {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return "미측정";
  }
  return `${value.toLocaleString("ko-KR")}${unit}`;
}

export function formatPercent(value: number | null | undefined, digits = 1): string {
  if (value === null || value === undefined || !Number.isFinite(value)) {
    return "미측정";
  }
  return `${(value * 100).toLocaleString("ko-KR", {
    maximumFractionDigits: digits,
    minimumFractionDigits: digits,
  })}%`;
}

export function formatDate(value: string | null | undefined): string {
  if (!value) {
    return "날짜 없음";
  }
  return value.slice(0, 10);
}
