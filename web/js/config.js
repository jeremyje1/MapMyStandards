// Global configuration for MapMyStandards Frontend
// Single source of truth for API base and feature flags

(function(){
  const fromEnv = {
    API_BASE_URL: window.__MMS_API_BASE__ || undefined,
    PLATFORM_BASE_URL: window.__MMS_PLATFORM_BASE__ || undefined,
  };

  const host = window.location.hostname;
  const defaults = {
    API_BASE_URL: host === 'localhost' ? 'http://localhost:8000' : 'https://api.mapmystandards.ai',
    PLATFORM_BASE_URL: host === 'localhost' ? 'http://localhost:3000' : 'https://platform.mapmystandards.ai',
    FEATURE_FLAGS: {
      enableRiskOverview: true,
      enableNarrativeExport: true
    }
  };

  window.MMS_CONFIG = Object.freeze({
    API_BASE_URL: fromEnv.API_BASE_URL || defaults.API_BASE_URL,
    PLATFORM_BASE_URL: fromEnv.PLATFORM_BASE_URL || defaults.PLATFORM_BASE_URL,
    FEATURE_FLAGS: defaults.FEATURE_FLAGS
  });
})();
