"use client";

import type { ReactNode } from "react";
import { Button, Dialog, DialogTrigger, Popover } from "react-aria-components";
import { ChevronDown } from "lucide-react";
import { StatusBadge } from "@/components/status-badge";
import styles from "./reporting-status.module.css";

type Props = {
  title?: string;
  receivedCount?: number;
  expectedCount?: number;
  /** Details shown in a popover when the box is clicked, e.g. pending report tables. */
  children?: ReactNode;
  detailsLabel?: string;
  /** Green badge shown when every expected report has come in. */
  completeLabel?: string;
};

/**
 * Reporting status box for the summary bar: how many of the expected reports
 * have come in, and how many are still pending (or "Complete" when none are).
 * Shows a dash until the counts are passed in. When details are passed as
 * children, the box opens them in a popover.
 */
export const ReportingStatus = ({
  title = "Reporting Status",
  receivedCount,
  expectedCount,
  children,
  detailsLabel = "Pending reports",
  completeLabel = "Complete",
}: Props) => {
  const hasCounts = receivedCount !== undefined && expectedCount !== undefined;
  const pendingCount = hasCounts ? expectedCount - receivedCount : 0;
  const hasDetails = Boolean(children);

  const summary = (
    <>
      <span className={styles.text}>
        <span className={styles.title}>{title}</span>
        <span className={styles.summary}>
          {hasCounts ? `${receivedCount} of ${expectedCount} reports received` : "—"}
        </span>
      </span>
      {pendingCount > 0 && <StatusBadge>{pendingCount} Pending</StatusBadge>}
      {hasCounts && pendingCount === 0 && <StatusBadge variant="success">{completeLabel}</StatusBadge>}
      {/* Greyed out when there are no details to open. */}
      <ChevronDown
        className={hasDetails ? styles.chevron : `${styles.chevron} ${styles.chevronDisabled}`}
        size={16}
        aria-hidden="true"
      />
    </>
  );

  if (!hasDetails) {
    return <div className={styles.status}>{summary}</div>;
  }

  return (
    <DialogTrigger>
      <Button className={styles.status}>{summary}</Button>
      <Popover className={styles.popover} placement="bottom end" offset={4}>
        <Dialog className={styles.details} aria-label={detailsLabel}>
          {children}
        </Dialog>
      </Popover>
    </DialogTrigger>
  );
};
