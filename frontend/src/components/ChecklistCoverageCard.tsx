import React, { useCallback, useEffect, useState } from 'react';
import api from '../services/api';

const ChecklistCoverageCard: React.FC<{ accreditor?: string }> = ({ accreditor }) => {
  const [coverage, setCoverage] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await api.standards.getChecklistStats({ accreditor });
      setCoverage(data.coverage_percentage || data.coverage_percent || 0);
    } catch (e) {
      setCoverage(0);
    } finally {
      setLoading(false);
    }
  }, [accreditor]);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-500">Checklist Coverage</p>
          <p className="text-3xl font-bold text-gray-900">{loading ? '—' : `${coverage}%`}</p>
        </div>
        <div className="text-xs text-gray-500">{accreditor || 'Primary Accreditor'}</div>
      </div>
    </div>
  );
};

export default ChecklistCoverageCard;
