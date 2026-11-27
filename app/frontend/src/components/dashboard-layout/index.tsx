import type { ReactNode } from "react";
import { ConfidentialityBanner } from "@/components/confidentiality-banner";
import { DashboardHeader } from "@/components/dashboard-header";
import { DashboardSidebar } from "@/components/dashboard-sidebar";
import { MinimalFooter } from "@/components/minimal-footer";

type Props = {
  displayName: string;
  orgName?: string;
  homeHref?: string;
  showAdmin?: boolean;
  children: ReactNode;
};

/**
 * The frame shared by every signed-in page: confidentiality banner across the
 * top, nav bar down the left, and the header, page content and footer to the
 * right of the nav bar.
 */
export function DashboardLayout({ displayName, orgName, homeHref, showAdmin, children }: Props) {
  return (
    <div className="dashboard-page">
      <ConfidentialityBanner />
      <div className="dashboard-shell">
        <DashboardSidebar homeHref={homeHref} showAdmin={showAdmin} />
        <div className="dashboard-right">
          <DashboardHeader displayName={displayName} orgName={orgName} />
          {children}
          <MinimalFooter />
        </div>
      </div>
    </div>
  );
}
