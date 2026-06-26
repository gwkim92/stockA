import { userFacingRecommendationText } from "./recommendation-panel-format";

type RecommendationResearchListProps = {
  readonly title: string;
  readonly items: readonly string[];
  readonly emptyText: string;
};

export function RecommendationResearchList({ title, items, emptyText }: RecommendationResearchListProps) {
  return (
    <article className="detail-path-card" style={{ minHeight: "180px" }}>
      <span>{title}</span>
      {items.length > 0 ? (
        items.map((item) => <p key={item}>{userFacingRecommendationText(item)}</p>)
      ) : (
        <p>{emptyText}</p>
      )}
    </article>
  );
}
