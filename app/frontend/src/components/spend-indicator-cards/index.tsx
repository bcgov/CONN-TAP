"use client";

import type { IndicatorItem } from "@/lib/chart-utils";
import { fmtMillionsFixed } from "@/lib/format-utils";
import styles from "./spend-indicator-cards.module.css";

type Props = {
  indicators: IndicatorItem[];
  dateRangeLabel?: string;
  isLoading?: boolean;
};

export const SpendIndicatorCards = ({ indicators, dateRangeLabel, isLoading }: Props) => (
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
              <p className={styles.cardValue}>{fmtMillionsFixed(item.value_millions)}</p>
            </div>
          ))}
    </div>
  </section>
);
