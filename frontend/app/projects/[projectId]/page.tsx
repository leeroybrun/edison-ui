/**
 * Project Dashboard page - the default view when opening a project.
 * This page shows project overview and health information.
 */
export default function ProjectDashboardPage({
  params,
}: {
  params: { projectId: string };
}) {
  return (
    <section className="space-y-4">
      <h1 className="text-2xl font-semibold text-gray-900">
        Project Dashboard
      </h1>
      <p className="text-gray-600">
        Project details for:{" "}
        <code className="rounded bg-gray-100 px-2 py-1">
          {params.projectId}
        </code>
      </p>
      <div className="rounded-lg border bg-white p-6">
        <p className="text-sm text-gray-500">
          Dashboard content coming soon. This will display project health,
          recent activity, and quick actions.
        </p>
      </div>
    </section>
  );
}
