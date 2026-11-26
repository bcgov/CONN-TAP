import styles from "./reporting-status.module.css";

type Props = {
  title?: string;
  receivedCount?: number;
  expectedCount?: number;
};

/**
 * Reporting status box for the summary bar: how many of the expected reports
 * have come in, and how many are still pending. Shows a dash until the counts
 * are passed in.
 */
export const ReportingStatus = ({
  title = "Reporting Status",
  receivedCount,
  expectedCount,
}: Props) => {
  const hasCounts = receivedCount !== undefined && expectedCount !== undefined;
  const pendingCount = hasCounts ? expectedCount - receivedCount : 0;

  return (
    <div className={styles.status}>
      <div className={styles.text}>
        <p className={styles.title}>{title}</p>
        <p className={styles.summary}>
          {hasCounts ? `${receivedCount} of ${expectedCount} reports received` : "—"}
        </p>
      </div>
      {pendingCount > 0 && <span className={styles.pending}>{pendingCount} Pending</span>}
    </div>
  );
};
