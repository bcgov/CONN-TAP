import { StatusBadge } from "@/components/status-badge";
import styles from "./pending-reports-table.module.css";

export type PendingReportsColumn = {
  key: string;
  label: string;
};

type Props = {
  title: string;
  description?: string;
  columns: PendingReportsColumn[];
  rows: Record<string, string>[];
  statusLabel?: string;
};

/**
 * A titled table of reports that haven't come in yet. Each row gets a status
 * badge in a final "Status" column.
 */
export const PendingReportsTable = ({
  title,
  description,
  columns,
  rows,
  statusLabel = "Pending",
}: Props) => (
  <section className={styles.section}>
    <h2 className={styles.title}>{title}</h2>
    {description && <p className={styles.description}>{description}</p>}
    <table className={styles.table}>
      <thead>
        <tr>
          {columns.map((column) => (
            <th key={column.key} scope="col">
              {column.label}
            </th>
          ))}
          <th scope="col">Status</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((row, index) => (
          <tr key={index}>
            {columns.map((column) => (
              <td key={column.key}>{row[column.key]}</td>
            ))}
            <td>
              <StatusBadge>{statusLabel}</StatusBadge>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  </section>
);
