"use client";

import { useMemo, useState } from "react";
import {
  MaterialReactTable,
  useMaterialReactTable,
  type MRT_Cell,
  type MRT_ColumnDef,
  type MRT_ColumnFiltersState,
  type MRT_ExpandedState,
  type MRT_FilterFn,
  type MRT_Row,
} from "material-react-table";
import { MinusSquare, PlusSquare } from "lucide-react";
import type { SummaryRow, SummaryTable } from "@/lib/chart-utils";
import { fmtMillions } from "@/lib/format-utils";
import styles from "./spend-summary-table.module.css";

type Props = {
  table: SummaryTable;
  dateRangeLabel?: string;
};

type TreeRow = SummaryRow & { subRows: TreeRow[] };

// Custom row toggle button. MRT's default is a rotating chevron; we use boxed
// +/- icons (the classic tree-expand look) instead.
const ExpandToggle = ({ row }: { row: MRT_Row<TreeRow> }) => {
  if (!row.getCanExpand()) return null;
  const isExpanded = row.getIsExpanded();
  const Icon = isExpanded ? MinusSquare : PlusSquare;
  return (
    <button
      type="button"
      className={styles.expandToggle}
      onClick={() => row.toggleExpanded()}
      aria-label={isExpanded ? "Collapse row" : "Expand row"}
      aria-expanded={isExpanded}
    >
      <Icon size={16} strokeWidth={2} aria-hidden />
    </button>
  );
};

// Filters
const nameFilter: MRT_FilterFn<TreeRow> = (row, _columnId, filterValue) => {
  const query = String(filterValue ?? "").trim().toLowerCase();
  if (!query) return true;
  return [row, ...row.getParentRows()].some((r) =>
    r.original.name.toLowerCase().includes(query),
  );
};

const typeFilter: MRT_FilterFn<TreeRow> = (row, _columnId, filterValue) => {
  const selected = (filterValue as string[]) ?? [];
  if (selected.length === 0) return true;
  return [row, ...row.getParentRows()].some((r) =>
    selected.includes(r.original.type),
  );
};

export const SpendSummaryTable = ({ table, dateRangeLabel }: Props) => {
  const [expanded, setExpanded] = useState<MRT_ExpandedState>({});
  const [globalFilter, setGlobalFilter] = useState("");
  const [columnFilters, setColumnFilters] = useState<MRT_ColumnFiltersState>([]);

  // Build the nested tree from the flat parent_id rows.
  const treeRows = useMemo<TreeRow[]>(() => {
    const nodes = new Map<string, TreeRow>();
    for (const row of table.rows) {
      nodes.set(row.id, { ...row, subRows: [] });
    }

    const roots: TreeRow[] = [];
    for (const row of table.rows) {
      const node = nodes.get(row.id)!;
      const parent = row.parent_id ? nodes.get(row.parent_id) : undefined;
      if (parent) parent.subRows.push(node);
      else roots.push(node);
    }

    return roots;
  }, [table.rows]);

  const typeOptions = useMemo(
    () => Array.from(new Set(table.rows.map((row) => row.type))),
    [table.rows],
  );

  const columns = useMemo<MRT_ColumnDef<TreeRow>[]>(() => {
    // Shared config for the right-aligned, currency-formatted spend columns.
    const moneyCell = ({ cell }: { cell: MRT_Cell<TreeRow> }) =>
      fmtMillions((cell.getValue() as number) ?? 0);
    const moneyColumn = {
      // Money values are short ("$0.27M"); keep the columns compact and let the
      // name column absorb the leftover width instead of scrolling horizontally.
      size: 120,
      minSize: 96,
      grow: true, // share the leftover width across the money columns
      filterVariant: "range", // min/max inputs, in millions; default betweenInclusive
      muiTableHeadCellProps: {
        align: "right",
        // Allow long category headers ("Other Professional Services") to wrap
        // rather than forcing the column wide.
        sx: { whiteSpace: "normal" },
      },
      muiTableBodyCellProps: { align: "right" },
      // Compact the range min/max inputs so they don't blow out the header width.
      muiFilterTextFieldProps: {
        sx: {
          m: 0,
          minWidth: "3rem",
          "& .MuiInputBase-input": { fontSize: "0.7rem", py: "2px", px: "4px" },
        },
      },
      Cell: moneyCell,
    } satisfies Partial<MRT_ColumnDef<TreeRow>>;

    // Match the compact 0.7rem filter text used by the money columns so every
    // filter input reads at the same smaller size.
    const smallFilterProps = {
      sx: { "& .MuiInputBase-input": { fontSize: "0.7rem" } },
    };

    // Extra styling the Type multi-select needs on top of the compact font.
    const typeFilterProps = {
      sx: {
        // Shrink the selected-value text shown in the field.
        "& .MuiInputBase-input, & .MuiSelect-select": { fontSize: "0.7rem" },
        // MRT renders each selected value as a full-size MUI Chip, which is
        // tall and heavily padded. Compact it to fit the row.
        "& .MuiChip-root": { height: "1.25rem", fontSize: "0.7rem" },
        "& .MuiChip-label": { px: "0.4rem" },
        // MRT reserves ~2rem + a 20px margin on the right for a clear-filter
        // button that's invisible until a value is set. On this narrow column
        // that shows as a big empty gap and truncates the "Filter by Type"
        // placeholder. Hide it — the caret still opens the menu, and options
        // are cleared by unchecking them or via the filter (funnel) toggle.
        "& .MuiInputAdornment-positionEnd": { display: "none" },
      },
      // The options render in a portal, out of reach of the field sx. MRT
      // merges our `slotProps.select` over its own, so route the menu styling
      // through MenuProps here (keep disableScrollLock, MRT's default).
      slotProps: {
        select: {
          MenuProps: {
            disableScrollLock: true,
            sx: {
              "& .MuiMenuItem-root": { fontSize: "0.8rem" },
              "& .MuiCheckbox-root": { padding: "4px" },
            },
          },
        },
      },
    };

    return [
      {
        accessorKey: "name",
        header: "BGE/Sub-org/SD",
        size: 280,
        minSize: 210,
        grow: false, // fixed; the money columns absorb the leftover width
        filterVariant: "text",
        filterFn: nameFilter,
        muiFilterTextFieldProps: smallFilterProps,
      },
      {
        accessorKey: "type",
        header: "Type",
        size: 116,
        minSize: 96,
        grow: false,
        // "Service Designee" wraps to two lines rather than widening the column.
        muiTableHeadCellProps: { sx: { whiteSpace: "normal" } },
        muiTableBodyCellProps: { sx: { whiteSpace: "normal" } },
        filterVariant: "multi-select",
        filterSelectOptions: typeOptions,
        filterFn: typeFilter,
        muiFilterTextFieldProps: typeFilterProps,
        // Expandable rows are roll-up totals of their children: label them
        // "<type>/Total" for display only. The accessor still returns the base
        // type, so the filter options stay BGE / Sub Org / Service Designee and
        // filtering by the base type still matches these rows.
        Cell: ({ row }) =>
          row.original.subRows.length > 0
            ? `${row.original.type}/Total`
            : row.original.type,
      },
      ...table.categories.map<MRT_ColumnDef<TreeRow>>((category) => ({
        ...moneyColumn,
        id: `cat_${category.code}`,
        header: category.name,
        accessorFn: (row) => row.values[category.code] ?? 0,
      })),
      {
        ...moneyColumn,
        accessorKey: "total",
        header: "Total Spend",
      },
    ];
  }, [table.categories, typeOptions]);

  const mrt = useMaterialReactTable({
    columns,
    data: treeRows,
    // Flex the columns to fill the card width (per-column `size`/`grow`) so the
    // table fits without horizontal scrolling.
    layoutMode: "grid",
    // Let users drag column borders to resize; widths update as they drag.
    enableColumnResizing: true,
    columnResizeMode: "onChange",
    // Keep the expand column tight so it doesn't leave a wide gap before the
    // name column, and swap MRT's rotating chevron for a plain +/- toggle.
    displayColumnDefOptions: {
      "mrt-row-expand": {
        size: 44,
        minSize: 44,
        grow: false,
        Cell: ExpandToggle,
      },
    },
    enableExpanding: true,
    getSubRows: (row) => row.subRows,
    filterFromLeafRows: true, // keep ancestors of rows that match a filter
    onExpandedChange: setExpanded,
    onGlobalFilterChange: setGlobalFilter,
    onColumnFiltersChange: setColumnFilters,
    state: {
      expanded,
      globalFilter,
      columnFilters,
    },
    // Rows are a fixed BGE > Sub-org > SD hierarchy; sorting would break that
    // ordering, so it's disabled.
    enableSorting: false,
    enableColumnFilters: true,
    enableColumnActions: false,
    enableColumnDragging: false,
    enablePagination: false,
    enableBottomToolbar: false,
    enableDensityToggle: false,
    enableFullScreenToggle: false,
    enableHiding: false,
    initialState: {
      density: "compact",
      showColumnFilters: false, // filters hidden until the funnel toggle is clicked
    },
    muiTablePaperProps: { elevation: 0, sx: { background: "transparent" } },
    muiTableBodyRowProps: ({ row }) =>
      row.original.level === 0
        ? { sx: { "& td, & th": { fontWeight: 700 }, background: "rgba(0,0,0,0.03)" } }
        : {},
  });

  if (table.rows.length === 0) {
    return <p className={styles.empty}>No data for this period.</p>;
  }

  return (
    <div className={styles.wrapper}>
      {dateRangeLabel && <p className={styles.dateRange}>{dateRangeLabel}</p>}
      <MaterialReactTable table={mrt} />
    </div>
  );
};
