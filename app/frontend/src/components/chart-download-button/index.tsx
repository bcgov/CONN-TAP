"use client";

import { useState } from "react";
import {
  Button,
  Menu,
  MenuItem,
  MenuTrigger,
  Popover,
} from "react-aria-components";
import { format } from "date-fns";
import { Download } from "lucide-react";
import { toJpeg, toPng } from "html-to-image";
import { jsPDF } from "jspdf";
import styles from "./chart-download-button.module.css";

export type ExportFormat = "png" | "jpeg" | "pdf" | "csv" | "xls";

export type CsvData = {
  headers: string[];
  rows: (string | number)[][];
};

const FORMAT_LABELS: Record<ExportFormat, string> = {
  png: "PNG",
  jpeg: "JPEG",
  pdf: "PDF",
  csv: "CSV",
  xls: "XLS",
};

// CSV and XLS aren't offered by default — they only show up once `csvData`
// is passed, or the caller explicitly opts in via `formats`.
const DEFAULT_FORMATS: ExportFormat[] = ["png", "jpeg", "pdf"];
const TABULAR_FORMATS = new Set<ExportFormat>(["csv", "xls"]);
const TABULAR_MIME_TYPES: Record<"csv" | "xls", string> = {
  csv: "text/csv;charset=utf-8;",
  xls: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
};

const IMAGE_OPTIONS = {
  backgroundColor: "#ffffff",
  pixelRatio: 2,
  quality: 0.95,
};
const IMAGE_EXPORTERS = { png: toPng, jpeg: toJpeg };

const triggerDownload = (href: string, filename: string) => {
  const link = document.createElement("a");
  link.download = filename;
  link.href = href;
  link.click();
};

// Same workbook feeds both writers, so CSV gets exceljs/fast-csv's escaping
// (quotes, embedded newlines, etc.) instead of a hand-rolled regex.
const buildTabularBuffer = async (
  format: "csv" | "xls",
  { headers, rows }: CsvData,
) => {
  const { Workbook } = await import("exceljs");
  const workbook = new Workbook();
  const sheet = workbook.addWorksheet("Sheet1");
  sheet.addRow(headers);
  for (const row of rows) sheet.addRow(row);
  return format === "csv"
    ? workbook.csv.writeBuffer()
    : workbook.xlsx.writeBuffer();
};

const isTabularFormat = (
  format: ExportFormat,
): format is "csv" | "xls" => TABULAR_FORMATS.has(format);

// filename format: {chart title} - YYYY Mon DD hh.mmaaa.{ext}
const buildFilename = (title: string, extension: string) =>
  `${title} - ${format(new Date(), "d MMM yyyy, h.mmaaa")}.${extension}`;

type ChartDownloadButtonProps = {
  targetRef: React.RefObject<HTMLElement | null>;
  title: string;
  label?: string;
  // When false, render in normal layout flow (e.g. inside a toolbar row)
  // instead of pinned to the card's top-right corner.
  floating?: boolean;
  // Which export formats to offer
  formats?: ExportFormat[];
  // Row data for the CSV/XLS options. Passing this makes both available even
  // without listing them in `formats`.
  csvData?: CsvData;
};

export const ChartDownloadButton = ({
  targetRef,
  title,
  label = "Download chart",
  floating = true,
  formats,
  csvData,
}: ChartDownloadButtonProps) => {
  const [isDownloading, setIsDownloading] = useState(false);
  const resolvedFormats =
    formats ??
    (csvData ? [...DEFAULT_FORMATS, ...TABULAR_FORMATS] : DEFAULT_FORMATS);
  const formatOptions = resolvedFormats
    .filter((value) => !isTabularFormat(value) || csvData)
    .map((value) => ({ value, label: FORMAT_LABELS[value] }));

  const handleDownload = async (format: ExportFormat) => {
    if (isDownloading) return;

    if (isTabularFormat(format)) {
      if (!csvData) return;
      setIsDownloading(true);
      try {
        const content = await buildTabularBuffer(format, csvData);
        const blob = new Blob([content], { type: TABULAR_MIME_TYPES[format] });
        const url = URL.createObjectURL(blob);
        const extension = format === "csv" ? "csv" : "xlsx";
        triggerDownload(url, buildFilename(title, extension));
        URL.revokeObjectURL(url);
      } finally {
        setIsDownloading(false);
      }
      return;
    }

    const node = targetRef.current;
    if (!node) return;

    setIsDownloading(true);
    try {
      // format PDF
      if (format === "pdf") {
        const dataUrl = await toPng(node, IMAGE_OPTIONS);
        const { width, height } = new jsPDF().getImageProperties(dataUrl);
        const pdf = new jsPDF({
          orientation: width >= height ? "landscape" : "portrait",
          unit: "px",
          format: [width, height],
        });
        pdf.addImage(dataUrl, "PNG", 0, 0, width, height);
        pdf.save(buildFilename(title, "pdf"));
      } else {
        // format PNG or JPEG
        const dataUrl = await IMAGE_EXPORTERS[format](node, IMAGE_OPTIONS);
        triggerDownload(dataUrl, buildFilename(title, format));
      }
    } finally {
      setIsDownloading(false);
    }
  };

  return (
    <div className={floating ? styles.wrapper : styles.wrapperInline}>
      <MenuTrigger>
        <Button
          className={styles.button}
          isDisabled={isDownloading}
          aria-label={label}
        >
          <Download size={16} aria-hidden="true" />
          Download
        </Button>
        <Popover>
          <Menu
            className={styles.menu}
            onAction={(key) => handleDownload(key as ExportFormat)}
          >
            {formatOptions.map((option) => (
              <MenuItem
                key={option.value}
                id={option.value}
                className={styles.menuItem}
              >
                {option.label}
              </MenuItem>
            ))}
          </Menu>
        </Popover>
      </MenuTrigger>
    </div>
  );
};
