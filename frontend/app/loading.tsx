export default function Loading() {
  return (
    <div
      role="status"
      aria-live="polite"
      className="flex min-h-[200px] items-center justify-center font-sans"
    >
      <div className="flex flex-col items-center gap-3">
        {/* Spinner */}
        <div
          className="h-8 w-8 animate-spin rounded-full border-4 border-gray-200 border-t-blue-600"
          aria-hidden="true"
        />
        <span className="text-sm text-gray-600">Loading...</span>
      </div>
    </div>
  );
}
