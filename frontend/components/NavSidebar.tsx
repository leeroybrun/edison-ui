import Link from "next/link";

export function NavSidebar() {
  return (
    <aside className="flex h-full w-64 flex-col border-r bg-gray-50 font-sans">
      {/* Top bar with app title */}
      <div className="flex h-14 items-center border-b px-4">
        <span className="font-semibold text-gray-900">Edison UI</span>
      </div>

      {/* Navigation links */}
      <nav aria-label="Main navigation" className="flex-1 p-4">
        <ul className="space-y-1">
          <li>
            <Link
              href="/"
              className="flex items-center rounded-md px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 hover:text-gray-900"
            >
              Dashboard
            </Link>
          </li>
          <li>
            <Link
              href="/projects"
              className="flex items-center rounded-md px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 hover:text-gray-900"
            >
              Projects
            </Link>
          </li>
          <li>
            <Link
              href="/settings"
              className="flex items-center rounded-md px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 hover:text-gray-900"
            >
              Settings
            </Link>
          </li>
        </ul>
      </nav>
    </aside>
  );
}
