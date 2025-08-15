"use client";
import { useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

// Disable static prerender so Next.js doesn't attempt to run useSession at build time
export const dynamic = 'force-dynamic';

export default function EnterpriseDashboardPage() {
  // During static export / prerender useSession can be undefined; guard.
  const sessionHook: any = (typeof window === 'undefined') ? { data: null, status: 'loading' } : useSession();
  const { data: session, status } = sessionHook;
  const router = useRouter();

  useEffect(() => {
    if (status === 'loading') return;
    const tier = (session?.user as any)?.tier;
    if (!session?.user) {
      router.replace('/auth/signin?callbackUrl=%2Fenterprise%2Fdashboard');
    } else if (tier !== 'enterprise' && tier !== 'system') {
      router.replace('/');
    }
  }, [session, status, router]);

  if (status === 'loading') return <p className="p-6">Loading...</p>;
  return (
    <div className="max-w-5xl mx-auto p-6 space-y-6">
      <h1 className="text-3xl font-semibold">Enterprise Control Center</h1>
      <p className="text-gray-600">Tier: {(session?.user as any)?.tier || 'n/a'}</p>
      <div className="grid gap-4 md:grid-cols-2">
        <section className="border rounded-md p-4">
          <h2 className="font-medium mb-2">Power BI Analytics</h2>
          <p className="text-sm mb-3">Embedded executive dashboards.</p>
            <a href="/enterprise/powerbi" className="text-blue-600 underline">Open analytics</a>
        </section>
        <section className="border rounded-md p-4">
          <h2 className="font-medium mb-2">Org Chart</h2>
          <p className="text-sm mb-3">Manage organizational structure for assessments.</p>
          <a href="/vault-mapping" className="text-blue-600 underline">Open org chart</a>
        </section>
      </div>
    </div>
  );
}
