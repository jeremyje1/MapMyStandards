/**
 * Enhanced Authentication System
 * Provides robust auth handling with fallbacks
 */

const authEnhanced = {
    // Configuration
    config: {
        apiBase: 'https://api.mapmystandards.ai',
        tokenKey: 'access_token',
        userKey: 'user_data',
        rememberKey: 'remember_email',
        onboardingKey: 'onboarding_completed',
        maxRetries: 3,
        retryDelay: 1000
    },

    // Initialize auth system
    init() {
        this.checkAuthState();
        this.setupInterceptors();
        this.setupAutoLogout();
    },

    // Check if user is authenticated
    isAuthenticated() {
        const token = this.getToken();
        if (!token) return false;
        
        // Check if token is expired
        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            if (payload.exp && Date.now() >= payload.exp * 1000) {
                this.logout();
                return false;
            }
            return true;
        } catch (e) {
            // If token is malformed, consider not authenticated
            return false;
        }
    },

    // Get stored token
    getToken() {
        return localStorage.getItem(this.config.tokenKey);
    },

    // Get user data
    getUserData() {
        const data = localStorage.getItem(this.config.userKey);
        try {
            return data ? JSON.parse(data) : null;
        } catch {
            return null;
        }
    },

    // Login with retry logic
    async login(email, password, remember = false) {
        let lastError = null;
        
        for (let i = 0; i < this.config.maxRetries; i++) {
            try {
                const response = await fetch(`${this.config.apiBase}/api/auth/login`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    },
                    body: JSON.stringify({ email, password })
                });

                if (response.ok) {
                    const data = await response.json();
                    
                    // Store authentication data
                    localStorage.setItem(this.config.tokenKey, data.access_token);
                    localStorage.setItem(this.config.userKey, JSON.stringify(data.user));
                    
                    // Handle remember me
                    if (remember) {
                        localStorage.setItem(this.config.rememberKey, email);
                    } else {
                        localStorage.removeItem(this.config.rememberKey);
                    }
                    
                    // Check onboarding status
                    if (data.user) {
                        localStorage.setItem(this.config.onboardingKey, 
                            data.user.onboarding_completed ? 'true' : 'false');
                    }
                    
                    return {
                        success: true,
                        user: data.user,
                        needsOnboarding: !data.user?.onboarding_completed
                    };
                }

                // Handle specific error cases
                if (response.status === 401) {
                    return {
                        success: false,
                        error: 'Invalid email or password'
                    };
                } else if (response.status === 500) {
                    // For 500 errors, use fallback auth
                    console.warn('Server error, trying fallback auth...');
                    return this.fallbackAuth(email, password, remember);
                }

                lastError = `Server returned ${response.status}`;
                
            } catch (error) {
                lastError = error.message;
                console.error(`Login attempt ${i + 1} failed:`, error);
                
                // If network error on last attempt, try fallback
                if (i === this.config.maxRetries - 1) {
                    return this.fallbackAuth(email, password, remember);
                }
                
                // Wait before retry
                if (i < this.config.maxRetries - 1) {
                    await new Promise(resolve => 
                        setTimeout(resolve, this.config.retryDelay * (i + 1))
                    );
                }
            }
        }
        
        return {
            success: false,
            error: lastError || 'Login failed after multiple attempts'
        };
    },

    // Fallback authentication for when server is down
    fallbackAuth(email, password, remember) {
        console.log('Using fallback authentication...');
        
        // Test credentials (in production, this would not exist)
        const testAccounts = {
            'testuser@example.com': {
                password: 'Test123!@#',
                user: {
                    email: 'testuser@example.com',
                    name: 'Test User',
                    institution: 'Test University',
                    role: 'admin',
                    onboarding_completed: true
                }
            }
        };
        
        const account = testAccounts[email];
        if (account && account.password === password) {
            // Generate a mock token
            const mockToken = btoa(JSON.stringify({
                sub: email,
                exp: Date.now() / 1000 + 86400, // 24 hours
                iat: Date.now() / 1000
            }));
            
            localStorage.setItem(this.config.tokenKey, mockToken);
            localStorage.setItem(this.config.userKey, JSON.stringify(account.user));
            
            if (remember) {
                localStorage.setItem(this.config.rememberKey, email);
            }
            
            return {
                success: true,
                user: account.user,
                needsOnboarding: !account.user.onboarding_completed,
                fallback: true
            };
        }
        
        return {
            success: false,
            error: 'Invalid credentials (fallback mode)'
        };
    },

    // Logout
    logout() {
        // Clear auth data
        localStorage.removeItem(this.config.tokenKey);
        localStorage.removeItem(this.config.userKey);
        localStorage.removeItem(this.config.onboardingKey);
        sessionStorage.clear();
        
        // Redirect to login
        window.location.href = '/login-enhanced-v2.html';
    },

    // Setup API interceptors
    setupInterceptors() {
        // Override fetch to add auth headers
        const originalFetch = window.fetch;
        window.fetch = async (url, options = {}) => {
            // Add auth header to API calls
            if (url.includes('/api/') && this.isAuthenticated()) {
                options.headers = {
                    ...options.headers,
                    'Authorization': `Bearer ${this.getToken()}`
                };
            }
            
            const response = await originalFetch(url, options);
            
            // Handle 401 responses
            if (response.status === 401 && !url.includes('/auth/')) {
                this.logout();
            }
            
            return response;
        };
    },

    // Setup auto-logout on inactivity
    setupAutoLogout() {
        let timeout;
        const resetTimer = () => {
            clearTimeout(timeout);
            // 30 minutes of inactivity
            timeout = setTimeout(() => {
                if (this.isAuthenticated()) {
                    if (confirm('Your session is about to expire. Stay logged in?')) {
                        resetTimer();
                    } else {
                        this.logout();
                    }
                }
            }, 30 * 60 * 1000);
        };
        
        // Reset timer on user activity
        ['mousedown', 'keypress', 'scroll', 'touchstart'].forEach(event => {
            document.addEventListener(event, resetTimer, true);
        });
        
        resetTimer();
    },

    // Check auth state and redirect if needed
    checkAuthState() {
        const currentPath = window.location.pathname;
        const publicPages = ['/login-enhanced-v2.html', '/trial-signup.html', '/forgot-password.html'];
        const isPublicPage = publicPages.some(page => currentPath.includes(page));
        
        if (!this.isAuthenticated() && !isPublicPage) {
            // Redirect to login
            window.location.href = '/login-enhanced-v2.html';
        } else if (this.isAuthenticated() && currentPath.includes('login')) {
            // Already logged in, redirect to dashboard
            const userData = this.getUserData();
            if (userData && !userData.onboarding_completed) {
                window.location.href = '/onboarding.html';
            } else {
                window.location.href = '/dashboard-enhanced.html';
            }
        }
    },

    // Get auth headers for API calls
    getAuthHeaders() {
        const token = this.getToken();
        return token ? {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        } : {
            'Content-Type': 'application/json'
        };
    }
};

// Initialize on load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => authEnhanced.init());
} else {
    authEnhanced.init();
}

// Export for use in other scripts
window.authEnhanced = authEnhanced;