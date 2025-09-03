export const metadata = { title: 'User Guide - MapMyStandards', description: 'Platform modules, workflows, and adoption patterns.' };

export default function UserGuidePage() {
  return (
    <div className="prose max-w-4xl">
      <h1>User Guide</h1>
      <p>This guide will surface platform module documentation inside the application UI.</p>
      <ol className="list-decimal pl-6">
        <li>Standards Graph Orientation</li>
        <li>Evidence Fabric Lifecycle</li>
        <li>Mapping & Reuse Patterns</li>
        <li>Narrative Assembly Flow</li>
        <li>Governance & Readiness Telemetry</li>
      </ol>
      <p>For now, view the extended version at <a className="text-blue-600 underline" href="/user-guide/" rel="noopener">/user-guide/</a>.</p>
    </div>
  );
}
