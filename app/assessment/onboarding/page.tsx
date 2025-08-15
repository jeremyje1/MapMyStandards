export default function OnboardingPage() {
  return (
    <div className="max-w-2xl mx-auto p-6 space-y-6">
      <h1 className="text-3xl font-semibold">Onboarding Checklist</h1>
      <ol className="list-decimal pl-6 space-y-2 text-gray-700">
        <li>Configure your organizational structure (Org Chart)</li>
        <li>Upload / map accreditation standards & evidence</li>
        <li>Invite team members (coming soon)</li>
        <li>Launch first assessment scenario</li>
        <li>Review AI-driven narrative insights</li>
      </ol>
      <p className="text-sm text-gray-500">Iterate this guided workflow as adoption grows.</p>
    </div>
  );
}
