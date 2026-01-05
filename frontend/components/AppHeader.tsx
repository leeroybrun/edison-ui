import Link from "next/link";

export function AppHeader() {
  return (
    <header className="border-b">
      <div className="mx-auto flex max-w-4xl items-center justify-between p-4">
        <Link href="/" className="font-semibold">
          Edison UI
        </Link>
        <nav className="flex items-center gap-4 text-sm text-gray-600">
          <Link href="/projects">Projects</Link>
        </nav>
      </div>
    </header>
  );
}
