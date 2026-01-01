import type { ReactNode } from "react";

import "./globals.css";
import { NavSidebar } from "../components/NavSidebar";

export const metadata = {
  title: "Edison UI",
  description: "Modern web dashboard for Edison project management",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className="flex h-screen font-sans">
        {/* Sidebar - hidden on mobile, visible on md+ */}
        <div className="hidden md:block">
          <NavSidebar />
        </div>

        {/* Main content area */}
        <div className="flex flex-1 flex-col">
          {/* Mobile header - visible on mobile only */}
          <header className="flex h-14 items-center border-b px-4 md:hidden">
            <span className="font-semibold text-gray-900">Edison UI</span>
          </header>

          {/* Mobile navigation - visible on mobile only */}
          <nav
            aria-label="Mobile navigation"
            className="flex gap-4 border-b px-4 py-2 text-sm md:hidden"
          >
            <a href="/" className="text-gray-700 hover:text-gray-900">
              Dashboard
            </a>
            <a href="/projects" className="text-gray-700 hover:text-gray-900">
              Projects
            </a>
          </nav>

          {/* Main content */}
          <main className="flex-1 overflow-auto p-4 md:p-6">{children}</main>
        </div>
      </body>
    </html>
  );
}
