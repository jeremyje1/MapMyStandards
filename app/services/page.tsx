export const metadata = { title: 'Services - MapMyStandards', description: 'Accreditation intelligence engine and advisory services.' };

export default function ServicesPage() {
  return (
    <div className="prose max-w-4xl">
      <h1>Services</h1>
      <p>The A³E Engine unifies evidence, standards mapping, narrative assembly, and governance telemetry.</p>
      <ul className="list-disc pl-6">
        <li>Standards Graph & Evidence Fabric</li>
        <li>Narrative Composer & Reuse Analytics</li>
        <li>Governance & Readiness Dashboards</li>
        <li>Advisory & Sponsored Pilots</li>
      </ul>
      <p>Marketing rich version will be hydrated from static HTML soon.</p>
    </div>
  );
}
