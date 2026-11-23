import styles from "./summary-stat.module.css";

type Props = {
  label: string;
  value: string;
  detail?: string;
};

/** A small labelled figure for a summary bar, e.g. "Peak Month / Jun 2026 / $9.1M". */
export const SummaryStat = ({ label, value, detail }: Props) => (
  <div className={styles.stat}>
    <p className={styles.label}>{label}</p>
    <p className={styles.value}>{value}</p>
    {detail && <p className={styles.detail}>{detail}</p>}
  </div>
);
