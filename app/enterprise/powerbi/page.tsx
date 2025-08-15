"use client";
import { useEffect, useRef, useState } from 'react';
import { useSession } from 'next-auth/react';
import { useRouter } from 'next/navigation';

export const dynamic = 'force-dynamic';

export default function PowerBIEmbedPage() {
  const sessionHook: any = (typeof window === 'undefined') ? { data: null, status: 'loading' } : useSession();
  const { data: session, status } = sessionHook;
  const router = useRouter();
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (status === 'loading') return;
    const tier = (session?.user as any)?.tier;
    if (!session?.user) {
      router.replace('/auth/signin?callbackUrl=%2Fenterprise%2Fpowerbi');
    } else if (tier !== 'enterprise' && tier !== 'system') {
      router.replace('/');
    }
  }, [session, status, router]);

  useEffect(() => {
    async function load() {
      if (!containerRef.current) return;
      try {
        const powerbiClient = await import('powerbi-client');
        const powerbi = new powerbiClient.service.Service(powerbiClient.factories.hpmFactory, powerbiClient.factories.wpmpFactory, powerbiClient.factories.routerFactory);
        const modelsNS = powerbiClient.models;
        const embedUrl = process.env.NEXT_PUBLIC_POWERBI_EMBED_URL;
        const reportId = process.env.NEXT_PUBLIC_POWERBI_REPORT_ID;
        const accessToken = process.env.NEXT_PUBLIC_POWERBI_ACCESS_TOKEN;
        if (!embedUrl || !reportId || !accessToken) {
          setError('Power BI environment variables not set');
          return;
        }
        const config: any = {
          type: 'report',
          id: reportId,
          embedUrl,
          accessToken,
          tokenType: modelsNS.TokenType.Embed,
          settings: { panes: { filters: { visible: false }, pageNavigation: { visible: true } } }
        };
        powerbi.embed(containerRef.current, config);
      } catch (e: any) {
        console.error('Power BI embed error', e);
        setError(e.message || 'Embed failed');
      }
    }
    load();
  }, []);

  if (status === 'loading') return <p className="p-6">Authorizing...</p>;
  if (error) return <div className="p-6 text-red-600">{error}</div>;
  return (
    <div className="p-4">
      <h1 className="text-2xl font-semibold mb-4">Executive Analytics</h1>
      <div ref={containerRef} className="w-full aspect-video border rounded" />
      <p className="text-xs text-gray-500 mt-2">Embed placeholder – replace with secure server token exchange.</p>
    </div>
  );
}
