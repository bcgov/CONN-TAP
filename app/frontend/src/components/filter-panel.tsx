import type { ReactNode } from "react";

export function FilterPanel({
  title = "Filters",
  children,
}: {
  title?: string;
  children?: ReactNode;
}) {
  return (
    <aside className="filter-panel" aria-label={title}>
      <div className="filter-panel__header">
        <h2 className="filter-panel__title">{title}</h2>
        {/* Buttons only for now; reset and close are not wired up yet. */}
        <div className="filter-panel__actions">
          <button type="button" className="filter-panel__reset">
            Reset all
          </button>
          <button type="button" className="filter-panel__close" aria-label="Close filters">
            ×
          </button>
        </div>
      </div>
      <div className="filter-panel__body">{children}</div>
    </aside>
  );
}
