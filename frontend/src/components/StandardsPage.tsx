import React, { useEffect, useMemo, useState } from 'react';
import api from '../services/api';

const ACCREDITORS = ['SACSCOC','HLC','MSCHE','WASC','NWCCU','NEASC'];

const StandardsPage: React.FC = () => {
  const [accreditor, setAccreditor] = useState<string>(() => {
    if (typeof window !== 'undefined') {
      const cached = window.localStorage.getItem('primary_accreditor');
      if (cached) return cached.toUpperCase();
    }
    return 'HLC';
  });
  const [checklist, setChecklist] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');

  const coverage = useMemo(() => {
    if (!checklist) return 0;
    return checklist.coverage_percentage || 0;
  }, [checklist]);

  const loadChecklist = async (acc: string) => {
    setLoading(true); setError('');
    try {
      const { data } = await api.standards.getChecklist({ accreditor: acc });
      setChecklist(data);
    } catch (e) {
      setError('Checklist not available yet. Using dashboard metrics for coverage.');
    } finally { setLoading(false); }
  };

  useEffect(() => {
    const init = async () => {
      // First render with localStorage-backed accreditor for snappy UI
      await loadChecklist(accreditor);
      // Then sync from backend settings and update if different
      try {
        const { data } = await api.raw.get('/api/user/intelligence-simple/settings');
        const acc = (data?.primary_accreditor || accreditor).toUpperCase();
        if (acc !== accreditor) {
          setAccreditor(acc);
          window.localStorage.setItem('primary_accreditor', acc);
          await loadChecklist(acc);
        }
      } catch {}
    };
    init();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold">Standards</h1>
        <div className="flex items-center gap-3">
          <label className="text-sm text-gray-600">Accreditor</label>
          <select
            className="border rounded px-2 py-1"
            value={accreditor}
            onChange={async (e) => {
              const v = e.target.value.toUpperCase();
              setAccreditor(v);
              try { await api.raw.post('/api/user/intelligence-simple/settings', { primary_accreditor: v }); } catch {}
              window.localStorage.setItem('primary_accreditor', v);
              loadChecklist(v);
            }}
          >
            {ACCREDITORS.map(a => <option key={a} value={a}>{a}</option>)}
          </select>
        </div>
      </div>
      {loading && <div>Loading…</div>}
  {error && <div className="text-yellow-700 bg-yellow-50 border border-yellow-200 rounded p-3 mb-4">{error}</div>}
      {checklist && (
        <div className="space-y-6">
          <div className="bg-white p-4 rounded shadow">
            <div className="text-sm text-gray-600">Checklist Coverage</div>
            <div className="text-3xl font-bold">{coverage}%</div>
            <div className="text-xs text-gray-500">{checklist.covered_items}/{checklist.total_items} items covered</div>
          </div>
          <div className="bg-white p-4 rounded shadow">
            <h2 className="text-lg font-semibold mb-2">Standards</h2>
            <div className="divide-y">
              {checklist.groups.map((g: any) => (
                <div key={g.standard_id} className="py-3">
                  <div className="font-medium">{g.title}</div>
                  <ul className="mt-2 grid md:grid-cols-2 gap-2">
                    {g.items.map((it: any) => (
                      <li key={it.standard_id} className="text-sm">
                        <span className={"inline-block w-2 h-2 rounded-full mr-2 " + (it.covered ? 'bg-green-500' : 'bg-gray-300')}></span>
                        <span className="font-medium">{it.title}</span>
                        <span className="text-gray-500"> — {it.level}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default StandardsPage;
