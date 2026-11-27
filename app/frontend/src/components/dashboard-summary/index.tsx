import type { ReactNode } from "react";
import styles from "./dashboard-summary.module.css";

type DashboardSummaryProps = {
  children: ReactNode;
  label?: string;
};

/**
 * White summary card at the top of a dashboard. Lays out the figures passed
 * in as children (e.g. SpendBreakdown, SummaryStat, ReportingStatus) in a row.
 */
export function DashboardSummary({ children, label = "Dashboard summary" }: DashboardSummaryProps) {
  return (
    <section className={styles.summary} aria-label={label}>
      {children}
    </section>
  );
}
