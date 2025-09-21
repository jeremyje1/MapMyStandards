import React, { useEffect, useState } from 'react';
import api from '../services/api';

const ACCREDITORS = ['SACSCOC','HLC','MSCHE','WASC','NWCCU','NEASC'];

const ReportsPage: React.FC = () => {
  const [accreditor, setAccreditor] = useState<string>(() => {
    if (typeof window !== 'undefined') {
      const cached = window.localStorage.getItem('primary_accreditor');
      if (cached) return cached.toUpperCase();
    }
    return 'HLC';
  });
  const [generating, setGenerating] = useState<boolean>(false);
  const [packPath, setPackPath] = useState<string>('');
  const [downloadUrl, setDownloadUrl] = useState<string>('');
  const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://api.mapmystandards.ai';
  const resolveApiUrl = (url?: string) => {
    if (!url) return '';
    if (/^https?:\/\//i.test(url)) return url;
    return `${API_BASE_URL.replace(/\/$/, '')}/${url.replace(/^\//, '')}`;
  };
  const [error, setError] = useState<string>('');

  const generatePack = async () => {
    setGenerating(true); setError(''); setPackPath('');
    try {
  const payload = { standard_ids: [] as string[], include_files: false, include_checklist: true, include_metrics: true, checklist_format: 'csv' as 'csv', accreditor };
      const { data } = await api.standards.exportReviewerPack(payload);
      if (data?.success && data?.pack_path) {
        setPackPath(data.pack_path);
        if (data.download_url) setDownloadUrl(data.download_url);
      } else {
        setError('Failed to generate reviewer pack');
      }
    } catch (e) {
      setError('Failed to generate reviewer pack');
    } finally { setGenerating(false); }
  };

  useEffect(() => {
    const init = async () => {
      // First show UI with localStorage-backed accreditor
      try {
        const { data } = await api.raw.get('/api/user/intelligence-simple/settings');
        const acc = (data?.primary_accreditor || accreditor).toUpperCase();
        if (acc !== accreditor) {
          setAccreditor(acc);
          window.localStorage.setItem('primary_accreditor', acc);
        }
      } catch {}
    };
    init();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-bold">Reports</h1>
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
            }}
          >
            {ACCREDITORS.map(a => <option key={a} value={a}>{a}</option>)}
          </select>
        </div>
      </div>
      <div className="bg-white p-4 rounded shadow">
        <button onClick={generatePack} disabled={generating} className="px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700 disabled:opacity-50">
          {generating ? 'Generating…' : 'Generate Reviewer Pack'}
        </button>
        {packPath && (
          <div className="mt-3 text-sm">
            Pack created at: <code>{packPath}</code>
            {downloadUrl && (
              <a className="ml-3 text-primary-600 hover:underline" href={resolveApiUrl(downloadUrl)} target="_blank" rel="noreferrer">Download</a>
            )}
          </div>
        )}
        {error && <div className="text-red-600 mt-2">{error}</div>}
      </div>
    </div>
  );
};

export default ReportsPage;
