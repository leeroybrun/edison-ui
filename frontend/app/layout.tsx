import type { ReactNode } from "react";

import "./globals.css";
import { AppHeader } from "../components/AppHeader";

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <AppHeader />
        <main className="mx-auto max-w-4xl p-4">{children}</main>
      </body>
    </html>
  );
}

