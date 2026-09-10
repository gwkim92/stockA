import Link from "next/link";
import type { Route } from "next";
import type { ApiResponse } from "@/lib/types";
export function CollectionPagination({ path, pageKey = "cursor", search, pagination, label }: {
  path: string; pageKey?: string; search: Record<string, string | undefined>;
  pagination: ApiResponse<unknown>["pagination"]; label: string;
}) {
  const href = (cursor?: string) => {
    const query = new URLSearchParams();
    for (const [key, value] of Object.entries(search)) if (value && key !== pageKey) query.set(key, value);
    if (cursor) query.set(pageKey, cursor);
    return `${path}${query.size ? `?${query}` : ""}` as Route;
  };
  return <nav className="collection-pagination" aria-label={`${label} 페이지`}>
    <span>{label} · 이 페이지 {pagination?.item_count ?? "미확인"}건</span>
    {search[pageKey] && <Link href={href()}>처음 페이지</Link>}
    {pagination?.has_more && pagination.next_cursor && <Link href={href(pagination.next_cursor)}>다음 페이지 →</Link>}
  </nav>;
}
