import type { ReactNode } from "react";
import styles from "./status-badge.module.css";

type Props = {
  children: ReactNode;
  /** "warning" is yellow (e.g. "Pending"), "success" is green (e.g. "Complete"). */
  variant?: "warning" | "success";
};

/** A small status label, e.g. "Pending" or "Complete". */
export const StatusBadge = ({ children, variant = "warning" }: Props) => (
  <span className={`${styles.badge} ${styles[variant]}`}>{children}</span>
);
