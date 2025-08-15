import React from 'react';

async function fetchStandards() {
  const res = await fetch(`${process.env.NEXT_PUBLIC_APP_URL || ''}/api/standards`, { cache: 'no-store' });
  const json = await res.json();
  return json.data || [];
}

export default async function StandardsPage() {
  const standards = await fetchStandards();
  return (
    <div className="max-w-5xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-4">Standards Frameworks</h1>
      <p className="text-sm text-gray-600 mb-6">Browse imported accreditation / compliance frameworks. Coverage metrics TBD.</p>
      <div className="space-y-4">
        {standards.map((s: any) => (
          <div key={s.id} className="border rounded p-4 bg-white shadow-sm">
            <div className="flex justify-between items-center">
              <div>
                <h2 className="font-semibold text-lg">{s.name} <span className="text-xs text-gray-500">{s.version}</span></h2>
                <p className="text-xs text-gray-500">{s.publisher}</p>
              </div>
              <a href={`/standards/${s.id}`} className="text-blue-600 text-sm underline">Open</a>
            </div>
          </div>
        ))}
        {!standards.length && <div className="text-sm text-gray-500">No standards imported yet.</div>}
      </div>
    </div>
  );
}
