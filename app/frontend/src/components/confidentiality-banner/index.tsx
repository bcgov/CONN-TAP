"use client";

import { useState } from "react";
import { AlertBanner } from "@bcgov/design-system-react-components";
import styles from "./confidentiality-banner.module.css";

export function ConfidentialityBanner() {
  const [dismissed, setDismissed] = useState(false);

  return (
    <div
      className={styles.collapse}
      data-dismissed={dismissed}
      aria-hidden={dismissed}
    >
      <div className={styles.clip}>
        <AlertBanner variant="info" onClose={() => setDismissed(true)}>
          <div className={styles.content}>
            <strong>Confidentiality Alert</strong>
            <span>
              This site is intended exclusively for authorized BGE and Administrator
              users. Users are bound by NGTA/Participation Agreement and must keep
              Provider&apos;s pricing and all information contained on the site
              confidential.
            </span>
          </div>
        </AlertBanner>
      </div>
    </div>
  );
}
