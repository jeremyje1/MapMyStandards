import React from 'react';

async function fetchSummary() {
  const res = await fetch(`${process.env.NEXT_PUBLIC_APP_URL || ''}/api/dashboard/summary`, { cache: 'no-store' });
  const json = await res.json();
  return json.data || {};
}

async function fetchTrends() {
  const res = await fetch(`${process.env.NEXT_PUBLIC_APP_URL || ''}/api/dashboard/trends`, { cache: 'no-store' });
  const json = await res.json();
  return json.data?.series || [];
}

export default async function DashboardPage() {
  const [summary, trends] = await Promise.all([fetchSummary(), fetchTrends()]);
  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      <h1 className="text-2xl font-bold">Real-time Dashboard</h1>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card label="Coverage %" value={summary.coveragePct?.toFixed(1) || '0'} />
        <Card label="Standards Items" value={summary.totalItems} />
        <Card label="Mapped Items" value={summary.mappedItems} />
        <Card label="Documents" value={summary.docs} />
        <Card label="Evidence Links" value={summary.evidence} />
        <Card label="Confirmed" value={summary.confirmed} />
        <Card label="Auto" value={summary.auto} />
        <Card label="Stale" value={summary.stale} />
      </div>
      <div className="bg-white border rounded p-4 shadow-sm">
        <h2 className="font-semibold mb-2">Evidence Trend (last 30d)</h2>
        <TrendChart data={trends} />
      </div>
      <div className="bg-white border rounded p-4 shadow-sm">
        <h2 className="font-semibold mb-2">Gaps By Level</h2>
        <pre className="text-xs overflow-auto">{JSON.stringify(summary.gapsByLevel, null, 2)}</pre>
      </div>
    </div>
  );
}

function Card({ label, value }: { label: string; value: any }) {
  return (
    <div className="p-4 bg-white border rounded shadow-sm flex flex-col">
      <span className="text-xs uppercase tracking-wide text-gray-500">{label}</span>
      <span className="text-xl font-semibold">{value ?? '-'}</span>
    </div>
  );
}

function TrendChart({ data }: { data: any[] }) {
  if (!data.length) return <div className="text-xs text-gray-500">No data.</div>;
  // Simple ASCII sparkline substitute
  const max = Math.max(...data.map(d => d.total));
  return (
    <div className="flex gap-1 items-end h-24">
      {data.map(d => (
        <div key={d.date} title={`${d.date} total:${d.total}`} className="bg-blue-500" style={{ height: `${(d.total / max)*100}%`, width: '6px' }} />
      ))}
    </div>
  );
}
