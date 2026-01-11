import type { ReactNode } from "react";

import { NavSidebar } from "../../components/NavSidebar";

/**
 * Layout for main (non-project) pages.
 * Provides the global NavSidebar navigation.
 */
export default function MainLayout({ children }: { children: ReactNode }) {
  return (
    <div className="flex h-full">
      {/* Sidebar - hidden on mobile, visible on md+ */}
      <div className="hidden md:block">
        <NavSidebar />
      </div>

      {/* Main content area */}
      <div className="flex min-w-0 flex-1 flex-col">
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
          <a href="/settings" className="text-gray-700 hover:text-gray-900">
            Settings
          </a>
        </nav>

        {/* Main content */}
        <main className="min-w-0 flex-1 overflow-auto p-4 md:p-6">
          {children}
        </main>
      </div>
    </div>
  );
}
