import React, { useEffect, useMemo, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import api from '../services/api';

const CrosswalkPage: React.FC = () => {
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState<string>('');
  const location = useLocation();

  const focusedStandard = useMemo(() => {
    const params = new URLSearchParams(location.search || '');
    return params.get('standard') || params.get('standard_id') || '';
  }, [location.search]);

  const focusedAccreditor = useMemo(() => {
    const params = new URLSearchParams(location.search || '');
    return params.get('accreditor') || '';
  }, [location.search]);

  const load = async () => {
    try {
      const resp = await api.raw.get('/api/user/intelligence-simple/evidence/crosswalk');
      setData(resp.data);
    } catch (e) {
      setError('Failed to load crosswalk');
    }
  };

  useEffect(() => {
    load();
  }, []);

  const focusedEvidence = useMemo(() => {
    if (!focusedStandard || !data?.matrix) return [] as string[];
    const matrix = data.matrix as Record<string, Record<string, number | boolean>>;
    return Object.entries(matrix)
      .filter(([, standards]) => Boolean(standards && standards[focusedStandard]))
      .map(([filename]) => filename)
      .sort();
  }, [data, focusedStandard]);

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">CrosswalkX</h1>
      {error && <div className="text-red-600">{error}</div>}
      {data && (
        <div className="space-y-4 rounded bg-white p-4 shadow">
          <div className="text-sm text-gray-600">Evidence files: {data.evidence.length} · Standards: {data.standards.length}</div>
          <div className="text-sm text-gray-600">Reuse Percentage: {data.reuse_percentage}% · Multi-use Files: {data.multi_use_count}</div>
          {focusedStandard ? (
            <div className="rounded border border-primary-100 bg-primary-50 px-3 py-2 text-sm text-primary-800">
              <div className="flex items-center justify-between gap-2">
                <div>
                  <div className="text-xs font-semibold uppercase tracking-wide text-primary-600">Focused standard</div>
                  <div className="font-semibold text-gray-900">{focusedStandard}</div>
                  {focusedAccreditor ? (
                    <div className="text-xs text-primary-600">{focusedAccreditor.toUpperCase()}</div>
                  ) : null}
                </div>
                <Link to="/standards" className="text-xs font-semibold text-primary-600 hover:text-primary-700">
                  Return to explorer
                </Link>
              </div>
              <div className="mt-2 text-xs text-primary-700">
                {focusedEvidence.length ? (
                  <span>{focusedEvidence.length} evidence file{focusedEvidence.length === 1 ? '' : 's'} mapped to this requirement:</span>
                ) : (
                  <span>No evidence currently mapped to this standard yet. Upload documents from the Standards Explorer to surface crosswalk links.</span>
                )}
              </div>
              {focusedEvidence.length ? (
                <ul className="mt-2 space-y-1 text-xs text-primary-800">
                  {focusedEvidence.map((filename) => (
                    <li key={filename} className="rounded bg-white/70 px-2 py-1">
                      {filename}
                    </li>
                  ))}
                </ul>
              ) : null}
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
};

export default CrosswalkPage;
