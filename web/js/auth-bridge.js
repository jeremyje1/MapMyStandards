/**
 * Authentication Bridge for Cross-Domain Session Management
 * Handles authentication state when cookies can't be shared across domains
 */

(function() {
    // Skip auth bridge on production domain - cookies work natively there
    if (window.location.hostname === 'platform.mapmystandards.ai') {
        console.log('[Auth Bridge] Skipped - running on production domain');
        return;
    }
    
    console.log('[Auth Bridge] Activated - running on', window.location.hostname);
    // Store auth state in sessionStorage as a backup
    window.MMS_AUTH_BRIDGE = {
        // Store authentication info when successful
        storeAuth: function(authData) {
            if (authData && authData.ok) {
                sessionStorage.setItem('mms:auth:email', authData.email || '');
                sessionStorage.setItem('mms:auth:active', 'true');
                sessionStorage.setItem('mms:auth:time', new Date().toISOString());
            }
        },
        
        // Get stored auth info
        getStoredAuth: function() {
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
            sessionStorage.removeItem('mms:auth:email');
            sessionStorage.removeItem('mms:auth:active');
            sessionStorage.removeItem('mms:auth:time');
        },
        
        // Enhanced auth check that tries multiple methods
        checkAuth: async function() {
            // First try the regular auth check
            try {
                const resp = await fetch(buildApiUrl('/api/auth/me'), {
                    credentials: 'include',
                    headers: { 'Accept': 'application/json' }
                });
                
                if (resp.ok) {
                    const data = await resp.json();
                    if (data && data.ok) {
                        this.storeAuth(data);
                        return data;
                    }
                }
            } catch (e) {
                console.error('Primary auth check failed:', e);
            }
            
            // Fall back to stored auth if available
            const stored = this.getStoredAuth();
            if (stored) {
                console.log('Using stored authentication');
                return stored;
            }
            
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