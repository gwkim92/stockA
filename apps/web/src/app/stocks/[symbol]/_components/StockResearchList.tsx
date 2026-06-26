import { stockText } from "./stock-detail-panel-format";

type StockResearchListProps = {
  readonly title: string;
  readonly items: readonly string[];
  readonly emptyText: string;
};

export function StockResearchList({ title, items, emptyText }: StockResearchListProps) {
  return (
    <article className="bento-card">
      <span className="metric-sub">{title}</span>
      <div className="bento-list compact-list">
        {items.length > 0 ? (
          items.map((item) => (
            <div className="bento-list-item" key={item}>
              {stockText(item)}
            </div>
          ))
        ) : (
          <div className="empty-state">{emptyText}</div>
        )}
      </div>
    </article>
  );
}
