/**
 * Authentication Bridge for Cross-Domain Session Management
 * Handles authentication state when cookies can't be shared across domains
 */

(function() {
    // Check if we're on production domain where cookies work natively
    const isProductionDomain = window.location.hostname === 'platform.mapmystandards.ai';
    
    if (isProductionDomain) {
        console.log('[Auth Bridge] Running on production domain - using native cookie auth');
    } else {
        console.log('[Auth Bridge] Activated - running on', window.location.hostname);
    }
    
    // Always define the auth bridge interface
    window.MMS_AUTH_BRIDGE = {
        // Store authentication info when successful
        storeAuth: function(authData) {
            // Store minimal flags off-prod; also persist token if present
            if (authData) {
                try {
                    const token = authData.access_token || (authData.data && authData.data.access_token) || '';
                    if (token) {
                        // Prefer localStorage for persistence; sessionStorage as fallback
                        try { localStorage.setItem('access_token', token); localStorage.setItem('jwt_token', token); localStorage.setItem('a3e_api_key', token); } catch(_){}
                        try { sessionStorage.setItem('access_token', token); sessionStorage.setItem('jwt_token', token); sessionStorage.setItem('a3e_api_key', token); } catch(_){}
                    }
                } catch(_){}
            }
            if (!isProductionDomain && authData && (authData.ok || authData.user)) {
                sessionStorage.setItem('mms:auth:email', (authData.email || (authData.user && authData.user.email) || ''));
                sessionStorage.setItem('mms:auth:active', 'true');
                sessionStorage.setItem('mms:auth:time', new Date().toISOString());
            }
        },
        
        // Get stored auth info
        getStoredAuth: function() {
            // On production, we don't use sessionStorage
            if (isProductionDomain) {
                return null;
            }
            
            const email = sessionStorage.getItem('mms:auth:email');
            const active = sessionStorage.getItem('mms:auth:active') === 'true';
            const time = sessionStorage.getItem('mms:auth:time');
            
            // Check if auth is still fresh (within 24 hours)
            if (time) {
                const authTime = new Date(time);
                const now = new Date();
                const hoursSinceAuth = (now - authTime) / (1000 * 60 * 60);
                
                if (hoursSinceAuth > 24) {
                    this.clearAuth();
                    return null;
                }
            }
            
            return active ? { email, ok: true } : null;
        },
        
        // Clear stored auth
        clearAuth: function() {
            if (!isProductionDomain) {
                sessionStorage.removeItem('mms:auth:email');
                sessionStorage.removeItem('mms:auth:active');
                sessionStorage.removeItem('mms:auth:time');
            }
        },
        
        // Enhanced auth check that tries multiple methods
        checkAuth: async function() {
            // First try the regular auth check
            try {
                // Build the API URL properly using global config
                const BASE = (window.MMS_CONFIG && window.MMS_CONFIG.API_BASE_URL) || '/api';
                const buildUrl = (path) => {
                    if (path.startsWith('http')) return path;
                    const base = BASE || '';
                    if (!base) return path;
                    if (base === '/api' && path.startsWith('/api/')) return path;
                    if (base.endsWith('/api') && path.startsWith('/api/')) return base + path.slice(4);
                    return base + (path.startsWith('/') ? path : '/' + path);
                };
                const apiUrl = buildUrl('/api/auth/me');
                
                console.log('[Auth Bridge] Checking auth at:', apiUrl);
                    
                const resp = await fetch(apiUrl, {
                    credentials: 'include',
                    headers: { 'Accept': 'application/json' }
                });
                
                console.log('[Auth Bridge] Auth check response:', resp.status);
                
                if (resp.ok) {
                    const data = await resp.json();
                    console.log('[Auth Bridge] Auth data:', data);
                    if (data && data.ok) {
                        this.storeAuth(data);
                        return data;
                    }
                }
                
                // If not OK, log the response
                const errorData = await resp.text();
                console.log('[Auth Bridge] Auth check failed:', errorData);
            } catch (e) {
                console.error('[Auth Bridge] Primary auth check error:', e);
            }
            
            // Fall back to stored auth if available (non-production only)
            const stored = this.getStoredAuth();
            if (stored) {
                console.log('[Auth Bridge] Using stored authentication');
                return stored;
            }
            
            console.log('[Auth Bridge] No authentication found');
            return { ok: false };
        }
    };
    
    // Override the global checkAuthentication if it exists
    if (typeof window.checkAuthentication !== 'undefined') {
        window.originalCheckAuth = window.checkAuthentication;
    }
    
    // Global auth check function that uses the bridge
    window.checkAuthentication = async function() {
        const result = await window.MMS_AUTH_BRIDGE.checkAuth();
        return result && result.ok === true;
    };
})();