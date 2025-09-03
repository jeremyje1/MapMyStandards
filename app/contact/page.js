export const metadata = { title: 'Contact - MapMyStandards', description: 'Reach support, sales, or request a sponsored pilot.' };

export default function ContactPage() {
  return (
    <div className="prose max-w-3xl">
      <h1>Contact</h1>
      <p>Need help or want to accelerate accreditation workflows?</p>
      <ul className="list-disc pl-6">
        <li>Email: support@mapmystandards.ai</li>
        <li>Pilot Inquiries: <a className="text-blue-600" href="/contact?program=pilot">Request Sponsored Pilot</a></li>
        <li>Start Trial: <a className="text-blue-600" href="/landing?tier=department">Department Tier Trial</a></li>
      </ul>
    </div>
  );
}
