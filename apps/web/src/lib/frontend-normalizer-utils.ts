export type MutableRecord = Record<string, unknown>;

export function isRecord(value: unknown): value is MutableRecord {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

export function ensureRecord(parent: MutableRecord, key: string) {
  if (!isRecord(parent[key])) {
    parent[key] = {};
  }
  return parent[key] as MutableRecord;
}

export function ensureArray(parent: MutableRecord, key: string) {
  if (!Array.isArray(parent[key])) {
    parent[key] = [];
  }
  return parent[key] as unknown[];
}

export function withDefault<T>(record: MutableRecord, key: string, fallback: T) {
  if (record[key] === undefined || record[key] === null) {
    record[key] = fallback;
  }
}
