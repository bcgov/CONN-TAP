import type { Metadata } from "next";
import "@bcgov/bc-sans/css/BC_Sans.css";
import "@bcgov/design-tokens/css/variables.css";
import Providers from "./providers";
import "./globals.css";

export const metadata: Metadata = {
  title: "Telecom Access Point",
  description:
    "Explore dashboards, reports, contract information, spend and savings analytics, and key performance metrics for telecom services.",
  icons: {
    icon: [
      { url: "/icons/bcid-favicon-16x16.png", sizes: "16x16", type: "image/png" },
      { url: "/icons/bcid-favicon-32x32.png", sizes: "32x32", type: "image/png" },
      { url: "/icons/bcid-apple-icon.svg", type: "image/svg+xml" },
    ],
    apple: "/icons/bcid-apple-touch-icon.png",
  },
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
