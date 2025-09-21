import React, { useEffect, useState } from 'react';
import { Navigate } from 'react-router-dom';
import api from '../services/api';

const OnboardingGuard: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [loading, setLoading] = useState(true);
  const [needsOnboarding, setNeedsOnboarding] = useState(false);

  useEffect(() => {
    const check = async () => {
      try {
        const { data } = await api.raw.get('/api/user/intelligence-simple/settings');
        const primary = (data?.primary_accreditor || '').toString().trim();
        const has = Boolean(data?.has_onboarded);
        if (!primary || !has) setNeedsOnboarding(true);
      } catch {
        // If settings endpoint fails, be permissive (no redirect) to avoid loops
      } finally {
        setLoading(false);
      }
    };
    check();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (needsOnboarding) {
    return <Navigate to="/onboarding" replace />;
  }

  return <>{children}</>;
};

export default OnboardingGuard;
