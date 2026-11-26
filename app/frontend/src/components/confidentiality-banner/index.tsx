"use client";

import { useState, type ReactNode } from "react";
import { AlertBanner } from "@bcgov/design-system-react-components";
import styles from "./confidentiality-banner.module.css";

const DEFAULT_TITLE = "Confidentiality Alert";
const DEFAULT_MESSAGE =
  "This site is intended exclusively for authorized BGE and Administrator users. " +
  "Users are bound by NGTA/Participation Agreement and must keep Provider's " +
  "pricing and all information contained on the site confidential.";

type ConfidentialityBannerProps = {
  title?: string;
  children?: ReactNode;
  onClose?: () => void;
};

export function ConfidentialityBanner({
  title = DEFAULT_TITLE,
  children = DEFAULT_MESSAGE,
  onClose,
}: ConfidentialityBannerProps) {
  const [dismissed, setDismissed] = useState(false);

  function handleClose() {
    setDismissed(true);
    onClose?.();
  }

  return (
    <div
      className={styles.collapse}
      data-dismissed={dismissed}
      aria-hidden={dismissed}
    >
      <div className={styles.clip}>
        <AlertBanner variant="info" onClose={handleClose}>
          <div className={styles.content}>
            <strong className={styles.title}>{title}</strong>
            <span className={styles.message}>{children}</span>
          </div>
        </AlertBanner>
      </div>
    </div>
  );
}
