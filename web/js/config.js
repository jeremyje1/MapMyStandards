// Global configuration for MapMyStandards Frontend
// Single source of truth for API base and feature flags

(function(){
  const fromEnv = {
    API_BASE_URL: window.__MMS_API_BASE__ || undefined,
    PLATFORM_BASE_URL: window.__MMS_PLATFORM_BASE__ || undefined,
  };

  const host = window.location.hostname;
  const isLocal = host === 'localhost' || host.endsWith('.local');
  const isVercel = host.includes('vercel.app');
  const isPlatform = host === 'platform.mapmystandards.ai';
  const defaults = {
    // Use appropriate API URL based on deployment environment
  // Prefer same-origin /api on platform/vite/vercel to avoid third-party cookie issues; Vercel rewrites proxy to backend
  API_BASE_URL: isLocal ? 'http://localhost:8000' : (isPlatform ? '/api' : (isVercel ? '/api' : '/api')),
    PLATFORM_BASE_URL: isLocal ? 'http://localhost:3000' : 'https://platform.mapmystandards.ai',
    FEATURE_FLAGS: {
      enableRiskOverview: true,
      enableNarrativeExport: true,
      enableRecentReports: true,
      enableTutorialBanner: true
    }
  };

  window.MMS_CONFIG = Object.freeze({
    API_BASE_URL: (fromEnv.API_BASE_URL || defaults.API_BASE_URL),
    PLATFORM_BASE_URL: fromEnv.PLATFORM_BASE_URL || defaults.PLATFORM_BASE_URL,
    FEATURE_FLAGS: defaults.FEATURE_FLAGS
  });
})();
