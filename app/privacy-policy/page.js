export const metadata = { title: 'Privacy & Security - MapMyStandards', description: 'Data protection, governance, and security posture.' };

export default function PrivacyPage() {
  return (
    <div className="prose max-w-4xl">
      <h1>Privacy & Security</h1>
      <p>We apply encryption in transit and at rest, principle of least privilege, retention bounding, and continuous monitoring.</p>
      <h2>Core Controls</h2>
      <ul className="list-disc pl-6">
        <li>Encryption (TLS 1.2+, AES-256)</li>
        <li>Role-based access & audit trails</li>
        <li>Secure secret management</li>
        <li>Dependency vulnerability scanning</li>
        <li>Backup integrity verification</li>
      </ul>
    </div>
  );
}
