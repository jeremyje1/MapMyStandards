import React, { useState } from 'react';
import api from '../services/api';

const ReviewerPackAction: React.FC<{ accreditor?: string }> = ({ accreditor }) => {
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState('');
  const [portalUrl, setPortalUrl] = useState<string>('');

  const go = async () => {
    setBusy(true); setMsg('');
    try {
      const payload = { standard_ids: [] as string[], include_files: false, include_checklist: true, include_metrics: true, checklist_format: 'csv' as 'csv', accreditor };
      const { data } = await api.standards.exportReviewerPack(payload);
      if (data?.success && (data?.download_url || data?.pack_path)) {
        setMsg('Pack created. Publishing…');
        try {
          const pub = await api.raw.post('/api/user/intelligence-simple/narratives/reviewer-pack/publish');
          const publicUrl = pub.data?.public_url as string | undefined;
          if (publicUrl) {
            const apiBase = (process.env.REACT_APP_API_URL || 'https://api.mapmystandards.ai').replace(/\/$/, '');
            const portal = `${apiBase}/reviewer-portal?pack=${encodeURIComponent(publicUrl)}`;
            setPortalUrl(portal);
            setMsg('Reviewer Pack published');
          } else {
            setMsg('Pack created. Publish link unavailable.');
          }
        } catch {
          setMsg('Pack created. Failed to publish for portal.');
        }
      } else {
        setMsg('Failed to create reviewer pack');
      }
    } catch (e) {
      setMsg('Failed to create reviewer pack');
    } finally { setBusy(false); }
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow mb-8">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-sm font-medium text-gray-600">Reviewer Pack</div>
          <div className="text-xs text-gray-500">Narrative + Citations + Checklist + Metrics</div>
        </div>
        <button onClick={go} disabled={busy} className="px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700 disabled:opacity-50">
          {busy ? 'Building…' : 'Build Reviewer Pack'}
        </button>
      </div>
      {msg && <div className="text-xs text-gray-600 mt-2">{msg}{portalUrl && (
        <>
          {' '}- <a className="text-primary-600 underline" href={portalUrl} target="_blank" rel="noreferrer">Open in Reviewer Portal</a>
        </>
      )}</div>}
    </div>
  );
};

export default ReviewerPackAction;
