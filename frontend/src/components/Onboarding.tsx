import React, { useEffect, useState } from 'react';
import api from '../services/api';

const ACCREDITORS = ['SACSCOC','HLC','MSCHE','WASC','NWCCU','NEASC'];

const Onboarding: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [primaryAccreditor, setPrimaryAccreditor] = useState<string>('HLC');
  const [institutionName, setInstitutionName] = useState<string>('');
  const [displayName, setDisplayName] = useState<string>('');

  useEffect(() => {
    const init = async () => {
      try {
        const { data } = await api.raw.get('/api/user/intelligence-simple/settings');
        if (data?.primary_accreditor) {
          setPrimaryAccreditor(String(data.primary_accreditor).toUpperCase());
        }
        if (data?.organization || data?.institution_name) {
          setInstitutionName(String(data.organization || data.institution_name));
        }
        if (data?.display_name || data?.name) {
          setDisplayName(String(data.display_name || data.name));
        }
      } catch {
        /* ignore */
      } finally {
        setLoading(false);
      }
    };
    init();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    try {
      await api.raw.post('/api/user/intelligence-simple/settings', {
        primary_accreditor: primaryAccreditor,
        organization: institutionName,
        display_name: displayName,
        has_onboarded: true,
      });
      window.location.href = '/dashboard';
    } catch (err: any) {
      setError(err?.response?.data?.message || 'Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto bg-white p-6 rounded-lg shadow">
      <h1 className="text-2xl font-bold mb-2">Welcome to MapMyStandards</h1>
      <p className="text-sm text-gray-600 mb-6">Let’s personalize your experience so your dashboard reflects your institution and accreditor.</p>

      {error && (
        <div className="mb-4 rounded-md bg-red-50 p-3 text-sm text-red-700 border border-red-200">{error}</div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Institution / College Name</label>
          <input
            className="border rounded px-3 py-2 w-full"
            placeholder="e.g., Northpath Community College"
            value={institutionName}
            onChange={(e) => setInstitutionName(e.target.value)}
          />
          <p className="text-xs text-gray-500 mt-1">Shown across the app and included on reports.</p>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Your Display Name</label>
          <input
            className="border rounded px-3 py-2 w-full"
            placeholder="e.g., Dr. Jane Smith"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
          />
          <p className="text-xs text-gray-500 mt-1">Used for greetings and reviewer pack signatures.</p>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Primary Accreditor</label>
          <select
            className="border rounded px-3 py-2 w-full"
            value={primaryAccreditor}
            onChange={(e) => setPrimaryAccreditor(e.target.value.toUpperCase())}
          >
            {ACCREDITORS.map((a) => (
              <option key={a} value={a}>{a}</option>
            ))}
          </select>
          <p className="text-xs text-gray-500 mt-1">We’ll use this to show the correct standards and coverage.</p>
        </div>

        <div className="flex justify-end gap-3">
          <button
            type="button"
            onClick={async () => {
              try {
                setSaving(true);
                await api.raw.post('/api/user/intelligence-simple/settings', {
                  primary_accreditor: primaryAccreditor,
                  organization: institutionName,
                  display_name: displayName,
                  has_onboarded: true,
                });
              } catch {/* ignore */}
              window.location.href = '/dashboard';
            }}
            className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800"
          >
            Skip for now
          </button>
          <button
            type="submit"
            disabled={saving}
            className={`px-4 py-2 rounded text-white ${saving ? 'bg-primary-400' : 'bg-primary-600 hover:bg-primary-700'}`}
          >
            {saving ? 'Saving…' : 'Continue'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default Onboarding;
