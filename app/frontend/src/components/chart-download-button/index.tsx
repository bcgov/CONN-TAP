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

type ExportFormat = "png" | "jpeg" | "pdf";

const FORMAT_OPTIONS: { value: ExportFormat; label: string }[] = [
  { value: "png", label: "PNG" },
  { value: "jpeg", label: "JPEG" },
  { value: "pdf", label: "PDF" },
];

const IMAGE_OPTIONS = {
  backgroundColor: "#ffffff",
  pixelRatio: 2,
  quality: 0.95,
};
const IMAGE_EXPORTERS = { png: toPng, jpeg: toJpeg };

const triggerImageDownload = (href: string, filename: string) => {
  const link = document.createElement("a");
  link.download = filename;
  link.href = href;
  link.click();
};

// filename format: {chart title} - YYYY Mon DD hh.mmaaa.{ext}
const buildFilename = (title: string, extension: string) =>
  `${title} - ${format(new Date(), "d MMM yyyy, h.mmaaa")}.${extension}`;

type ChartDownloadButtonProps = {
  targetRef: React.RefObject<HTMLElement | null>;
  title: string;
  label?: string;
};

export const ChartDownloadButton = ({
  targetRef,
  title,
  label = "Download chart",
}: ChartDownloadButtonProps) => {
  const [isDownloading, setIsDownloading] = useState(false);

  const handleDownload = async (format: ExportFormat) => {
    const node = targetRef.current;
    if (!node || isDownloading) return;

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
        triggerImageDownload(dataUrl, buildFilename(title, format));
      }
    } finally {
      setIsDownloading(false);
    }
  };

  return (
    <div className={styles.wrapper}>
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
            {FORMAT_OPTIONS.map((option) => (
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
