// Standardized Navigation for MapMyStandards Platform
const NavigationManager = {
    // API base URL
    API_BASE: 'https://api.mapmystandards.ai',
    
    // Navigation HTML template
    getNavigationHTML(activePage = '') {
        return `
            <header class="header" style="background: white; border-bottom: 1px solid #e1e4e8; padding: 1rem 0; box-shadow: 0 1px 3px rgba(0,0,0,0.1); position: sticky; top: 0; z-index: 1000;">
                <div class="header-content" style="max-width: 1200px; margin: 0 auto; padding: 0 2rem; display: flex; justify-content: space-between; align-items: center;">
                    <a href="/dashboard.html" class="logo" style="display: flex; align-items: center; text-decoration: none; gap: 0.5rem;">
                        <img src="https://mapmystandards.ai/wp-content/uploads/2025/07/Original-Logo.png" alt="MapMyStandards" style="height: 40px;">
                        <span style="font-size: 1.5rem; font-weight: bold; color: #0F3875;">MapMyStandards</span>
                    </a>
                    <nav class="nav-links" style="display: flex; gap: 2rem;">
                        <a href="/dashboard.html" class="nav-link ${activePage === 'dashboard' ? 'active' : ''}" style="text-decoration: none; color: ${activePage === 'dashboard' ? '#0F3875' : '#586069'}; font-weight: 500;">Dashboard</a>
                        <a href="/documents.html" class="nav-link ${activePage === 'documents' ? 'active' : ''}" style="text-decoration: none; color: ${activePage === 'documents' ? '#0F3875' : '#586069'}; font-weight: 500;">Documents</a>
                        <a href="/upload.html" class="nav-link ${activePage === 'upload' ? 'active' : ''}" style="text-decoration: none; color: ${activePage === 'upload' ? '#0F3875' : '#586069'}; font-weight: 500;">Upload</a>
                        <a href="/reports-modern.html" class="nav-link ${activePage === 'reports' ? 'active' : ''}" style="text-decoration: none; color: ${activePage === 'reports' ? '#0F3875' : '#586069'}; font-weight: 500;">Reports</a>
                        <a href="/help" class="nav-link ${activePage === 'help' ? 'active' : ''}" style="text-decoration: none; color: ${activePage === 'help' ? '#0F3875' : '#586069'}; font-weight: 500;">Help</a>
                    </nav>
                    <div class="user-menu" style="display: flex; align-items: center; gap: 1rem;">
                        <span class="user-email" id="userEmail" style="color: #666; font-size: 0.9rem;">Loading...</span>
                        <button class="btn-logout" onclick="NavigationManager.logout()" style="background: #f0f0f0; border: none; padding: 0.5rem 1rem; border-radius: 5px; cursor: pointer; font-weight: 500;">Logout</button>
                    </div>
                </div>
            </header>
        `;
    },
    
    // Initialize navigation
    init(activePage = '') {
        // Check authentication
        const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
        if (!token && window.location.pathname !== '/login.html') {
            window.location.href = '/login.html';
            return;
        }
        
        // Load user info
        this.loadUserInfo();
        
        // Auto-refresh metrics every 30 seconds
        if (activePage === 'dashboard') {
            setInterval(() => {
                if (window.DashboardManager && window.DashboardManager.loadMetrics) {
                    window.DashboardManager.loadMetrics();
                }
            }, 30000);
        }
    },
    
    // Load and display user information
    async loadUserInfo() {
        // First try localStorage
        const storedEmail = localStorage.getItem('user_email');
        if (storedEmail) {
            const emailElement = document.getElementById('userEmail');
            if (emailElement) {
                emailElement.textContent = storedEmail;
            }
        }
        
        // Then try to get fresh data from API
        try {
            const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
            if (!token) return;
            
            const response = await fetch(`${this.API_BASE}/api/auth/me`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (response.ok) {
                const userData = await response.json();
                if (userData.email) {
                    localStorage.setItem('user_email', userData.email);
                    const emailElement = document.getElementById('userEmail');
                    if (emailElement) {
                        emailElement.textContent = userData.email;
                    }
                }
            }
        } catch (error) {
            console.error('Failed to load user info:', error);
        }
    },
    
    // Logout function
    logout() {
        // Clear all storage
        localStorage.clear();
        sessionStorage.clear();
        
        // Redirect to login
        window.location.href = '/login.html';
    },
    
    // Helper function to get current page
    getCurrentPage() {
        const path = window.location.pathname;
        if (path.includes('dashboard')) return 'dashboard';
        if (path.includes('documents')) return 'documents';
        if (path.includes('upload')) return 'upload';
        if (path.includes('report')) return 'reports';
        if (path.includes('help')) return 'help';
        return '';
    }
};

// Export for use in other scripts
window.NavigationManager = NavigationManager;