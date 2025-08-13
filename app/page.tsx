import Link from 'next/link';

export default function HomePage() {
  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-semibold">Welcome</h2>
      <p>Use passwordless email to sign in.</p>
      <Link className="text-blue-600 underline" href="/auth/signin">Go to Sign In</Link>
    </div>
  );
}
