import type { Metadata } from "next";
import "@bcgov/bc-sans/css/BC_Sans.css";
import Providers from "./providers";
import "./globals.css";

export const metadata: Metadata = {
  title: "Telecom Hub",
  description:
    "Explore dashboards, reports, contract information, spend and savings analytics, and key performance metrics for telecom services.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="telecom-landing">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
