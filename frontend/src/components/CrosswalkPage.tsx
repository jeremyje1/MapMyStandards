import React, { useEffect, useState } from 'react';
import api from '../services/api';

const CrosswalkPage: React.FC = () => {
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState<string>('');

  const load = async () => {
    try {
  const resp = await api.raw.get('/api/user/intelligence-simple/evidence/crosswalk');
  setData(resp.data);
    } catch (e) {
      setError('Failed to load crosswalk');
    }
  };

  useEffect(() => { load(); }, []);

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">CrosswalkX</h1>
      {error && <div className="text-red-600">{error}</div>}
      {data && (
        <div className="bg-white p-4 rounded shadow">
          <div className="text-sm text-gray-600 mb-2">Evidence files: {data.evidence.length} · Standards: {data.standards.length}</div>
          <div className="text-sm text-gray-600">Reuse Percentage: {data.reuse_percentage}% · Multi-use Files: {data.multi_use_count}</div>
        </div>
      )}
    </div>
  );
};

export default CrosswalkPage;
