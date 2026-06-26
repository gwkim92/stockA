import Link from "next/link";

import { NewsTitleBlock } from "@/components/news-title-block";
import { koCode, koLabel } from "@/lib/korean-labels";
import type { AiEvidenceNeighborhoodData } from "@/lib/types";

import {
  formatEventDate,
  formatStoryBasis,
  stockEventSourceDocumentHref,
  stockEventsHref,
} from "./stock-evidence-format";
import { formatPercent } from "./stock-detail-panel-format";

type StockStoryGroupSectionProps = {
  readonly neighborhood: AiEvidenceNeighborhoodData;
  readonly storyGroups: NonNullable<AiEvidenceNeighborhoodData["story_groups"]>;
};

export function StockStoryGroupSection({ neighborhood, storyGroups }: StockStoryGroupSectionProps) {
  return (
    <section className="stock-evidence-section" aria-label={`${neighborhood.symbol} 뉴스 이야기 묶음`}>
      <div className="stock-evidence-section-head">
        <div>
          <span>뉴스 묶음 이유</span>
          <h3>같은 이슈로 묶인 뉴스와 그 근거</h3>
        </div>
        <p>제목만 보지 않고, 테마·종목·원문 근거·묶음 신뢰도를 함께 본다.</p>
      </div>
      <div className="stock-story-card-grid">
        {storyGroups.slice(0, 4).map((group) => {
          const firstSource = stockEventSourceDocumentHref(group.source_document_ids[0] ?? null);
          return (
            <article className="stock-story-card" key={group.story_id}>
              <div className="stock-story-card-top">
                <span>{formatStoryBasis(group.basis)}</span>
                <strong>묶음 신뢰도 {formatPercent(group.confidence)}</strong>
              </div>
              <NewsTitleBlock
                compact
                title={group.title}
                koreanTitle={group.korean_title}
                koreanSummary={group.korean_summary}
                translationConfidence={group.translation_confidence}
                themeKey={group.theme_keys[0]}
              />
              <div className="stock-story-metrics">
                <span>이벤트 {group.event_count.toLocaleString("ko-KR")}개</span>
                <span>원천 {group.source_document_count.toLocaleString("ko-KR")}개</span>
                <span>원문 근거 {group.linked_chunk_count.toLocaleString("ko-KR")}개</span>
              </div>
              <div className="stock-story-reasons">
                {group.relation_reasons.slice(0, 3).map((reason) => (
                  <p key={`${group.story_id}-${reason}`}>묶인 이유: {koLabel(reason)}</p>
                ))}
              </div>
              {group.events.slice(0, 2).map((event) => (
                <div className="stock-story-event" key={`${group.story_id}-${event.event_id}`}>
                  <small>대표 이벤트 · {formatEventDate(event.event_at)} · {koCode(event.impact_direction)}</small>
                  <NewsTitleBlock
                    compact
                    title={event.title}
                    koreanTitle={event.korean_title}
                    koreanSummary={event.korean_summary}
                    translationConfidence={event.translation_confidence}
                    themeKey={event.theme_key}
                    impactDirection={event.impact_direction}
                    impactScore={event.impact_score}
                  />
                </div>
              ))}
              <div className="mini-link-stack">
                {firstSource ? <Link href={firstSource}>원천 문서</Link> : null}
                <Link href={stockEventsHref(neighborhood.symbol)}>수집 뉴스</Link>
              </div>
            </article>
          );
        })}
        {storyGroups.length === 0 ? (
          <p className="stock-evidence-empty">아직 같은 이야기로 묶을 수 있는 뉴스 근거가 없다.</p>
        ) : null}
      </div>
    </section>
  );
}
