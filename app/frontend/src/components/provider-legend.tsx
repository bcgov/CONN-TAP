"use client";

export type ProviderItem = {
  label: string;
  traceName: string;
  color: string;
};

type ProviderLegendProps = {
  providers: ProviderItem[];
  activeProviders: Set<string>;
  onToggle: (traceName: string) => void;
};

export function ProviderLegend({ providers, activeProviders, onToggle }: ProviderLegendProps) {
  return (
    <div className="dashboard-legend">
      <span className="dashboard-legend__label">Showing results for</span>
      {providers.map(({ label, traceName, color }) => (
        <button
          key={traceName}
          className={`dashboard-legend__btn${activeProviders.has(traceName) ? "" : " dashboard-legend__btn--off"}`}
          onClick={() => onToggle(traceName)}
          type="button"
        >
          <span className="dashboard-legend__dot" style={{ background: color }} />
          {label}
        </button>
      ))}
    </div>
  );
}
