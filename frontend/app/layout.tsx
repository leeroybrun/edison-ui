import type { ReactNode } from "react";

import "./globals.css";

export const metadata = {
  title: "Edison UI",
  description: "Modern web dashboard for Edison project management",
};

/**
 * Root layout provides the HTML shell only.
 * Page-specific layouts (main vs project) handle their own navigation.
 */
export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className="h-screen font-sans">{children}</body>
    </html>
  );
}
