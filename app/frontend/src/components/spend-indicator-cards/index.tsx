"use client";

import type { IndicatorItem } from "@/lib/chart-utils";
import styles from "./spend-indicator-cards.module.css";

function fmt(millions: number): string {
  return `$${millions.toFixed(1)}M`;
}

type Props = {
  indicators: IndicatorItem[];
  dateRangeLabel?: string;
  isLoading?: boolean;
};

export function SpendIndicatorCards({ indicators, dateRangeLabel, isLoading }: Props) {
  return (
    <section className={styles.section} aria-label="Spend totals">
      {dateRangeLabel && (
        <p className={styles.dateRange}>{dateRangeLabel}</p>
      )}
      <div className={styles.cards}>
        {isLoading
          ? [0, 1, 2].map((i) => (
              <div key={i} className={`${styles.card} ${styles.cardLoading}`}>
                <p className={styles.cardLabel}>Loading…</p>
                <p className={styles.cardValue}>—</p>
              </div>
            ))
          : indicators.map((item) => (
              <div key={item.label} className={styles.card}>
                <p className={styles.cardLabel}>{item.label}</p>
                <p className={styles.cardValue}>{fmt(item.value_millions)}</p>
              </div>
            ))}
      </div>
    </section>
  );
}
