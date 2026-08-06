"use client";

import {
  MaterialReactTable,
  useMaterialReactTable,
  type MRT_ColumnDef,
  type MRT_RowData,
  type MRT_TableOptions,
} from "material-react-table";
import styles from "./chart-data-table.module.css";

type Props<TData extends MRT_RowData> = {
  columns: MRT_ColumnDef<TData>[];
  data: TData[];
  emptyLabel?: string;
  // Escape hatch for per-chart MRT tweaks (sorting, filters, row styling…).
  options?: Partial<MRT_TableOptions<TData>>;
};

/**
 * The Table view behind every dashboard chart's Graph / Table toggle: each
 * chart supplies its own columns and rows, this owns the shared MRT setup so
 * the tables look and behave the same across cards.
 */
export function ChartDataTable<TData extends MRT_RowData>({
  columns,
  data,
  emptyLabel = "No data for this period.",
  options,
}: Props<TData>) {
  const table = useMaterialReactTable({
    columns,
    data,
    // Flex columns to the card width so tables fit without horizontal scroll.
    layoutMode: "grid",
    enableColumnResizing: false,
    enableSorting: false,
    enableColumnActions: false,
    enableColumnDragging: false,
    enableHiding: false,
    enablePagination: false,
    enableTopToolbar: false,
    enableBottomToolbar: false,
    enableDensityToggle: false,
    enableFullScreenToggle: false,
    initialState: { density: "compact" },
    muiTablePaperProps: { elevation: 0, sx: { background: "transparent" } },
    ...options,
  });

  if (data.length === 0) {
    return <p className={styles.empty}>{emptyLabel}</p>;
  }

  return (
    <div className={styles.wrapper}>
      <MaterialReactTable table={table} />
    </div>
  );
}
