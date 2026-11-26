"use client";

import { fmtMillions } from "@/lib/format-utils";
import styles from "./spend-breakdown.module.css";

export type SpendBreakdownItem = {
  label: string;
  valueMillions: number;
  percentage: number;
  colour: string;
};

type Props = {
  totalMillions: number;
  items: SpendBreakdownItem[];
  isLoading?: boolean;
};

/** A total spend figure with a bar showing how it splits between items (e.g. providers). */
export const SpendBreakdown = ({ totalMillions, items, isLoading = false }: Props) => {
  if (isLoading) {
    return (
      <div className={styles.breakdown}>
        <p className={styles.total}>—</p>
      </div>
    );
  }

  const barDescription = items
    .map((item) => `${item.label} ${Math.round(item.percentage)} percent`)
    .join("; ");

  return (
    <div className={styles.breakdown}>
      <p className={styles.total}>{fmtMillions(totalMillions)}</p>

      <div className={styles.labels}>
        {items.map((item) => (
          <p key={item.label} className={styles.label}>
            <span>
              {item.label} <span className={styles.amount}>{fmtMillions(item.valueMillions)}</span>
            </span>
            <span>{Math.round(item.percentage)}%</span>
          </p>
        ))}
      </div>

      <div className={styles.bar} role="img" aria-label={barDescription}>
        {items.map((item) => (
          <div
            key={item.label}
            className={styles.segment}
            style={{ width: `${item.percentage}%`, background: item.colour }}
          />
        ))}
      </div>
    </div>
  );
};
