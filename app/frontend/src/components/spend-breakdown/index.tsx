"use client";

import { fmtMillions } from "@/lib/format-utils";
import styles from "./spend-breakdown.module.css";

export type SpendBreakdownItem = {
  label: string;
  valueMillions: number;
  percentage: number;
  colour: string;
};

type SpendTotalProps = {
  totalMillions: number;
};

type SpendBreakdownPartsProps = {
  items: SpendBreakdownItem[];
};

type Props = {
  totalMillions: number;
  items: SpendBreakdownItem[];
  isLoading?: boolean;
};

/** The large total spend figure, e.g. "$7.0M". */
export const SpendTotal = ({ totalMillions }: SpendTotalProps) => (
  <p className={styles.total}>{fmtMillions(totalMillions)}</p>
);

/** One label per item, spread across the row: name, amount and percentage. */
export const SpendBreakdownLabels = ({ items }: SpendBreakdownPartsProps) => (
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
);

/** A bar split into one coloured segment per item, sized by its percentage. */
export const SpendBreakdownBar = ({ items }: SpendBreakdownPartsProps) => {
  const barDescription = items
    .map((item) => `${item.label} ${Math.round(item.percentage)} percent`)
    .join("; ");

  return (
    <div className={styles.bar} role="img" aria-label={barDescription}>
      {items.map((item) => (
        <div
          key={item.label}
          className={styles.segment}
          style={{ width: `${item.percentage}%`, background: item.colour }}
        />
      ))}
    </div>
  );
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

  return (
    <div className={styles.breakdown}>
      <SpendTotal totalMillions={totalMillions} />
      <SpendBreakdownLabels items={items} />
      <SpendBreakdownBar items={items} />
    </div>
  );
};
