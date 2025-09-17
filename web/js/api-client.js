/**
 * API Configuration for MapMyStandards Platform
 * Frontend Integration for Phase K
 */

// Configuration object for different environments
// Use shared config.js for API base
const config = { baseUrl: (window.MMS_CONFIG && window.MMS_CONFIG.API_BASE_URL) || 'https://api.mapmystandards.ai' };

/**
 * API Client for MapMyStandards Backend
 */
class MapMyStandardsAPI {
    constructor() {
        this.baseUrl = config.baseUrl;
        this.cookieAuth = true; // leverage HttpOnly cookies only
        this._refreshInFlight = null;
        this._auth = (typeof window !== 'undefined' && window.MMS_AUTH) ? window.MMS_AUTH : null;
    }

    // Common headers for API requests
    getHeaders(includeAuth = true) {
        const headers = {
            'Content-Type': 'application/json'
        };
        // No Authorization header; rely on HttpOnly cookies
        return headers;
    }

    // Generic API request method
    async request(endpoint, options = {}) {
        if (this._auth && typeof this._auth.request === 'function') {
            return await this._auth.request(endpoint, options);
        }
        const url = `${this.baseUrl}${endpoint}`;
        const defaultOptions = {
            headers: this.getHeaders(options.auth !== false),
            credentials: 'include',
            ...options
        };

        const attemptWithRetry = async (tries = 3) => {
            let last;
            for (let i = 0; i < tries; i++) {
                try {
                    const r = await fetch(url, defaultOptions);
                    if (r.status >= 500 && r.status <= 504) throw new Error(`upstream_${r.status}`);
                    return r;
                } catch (e) {
                    last = e;
                    await new Promise(r => setTimeout(r, 300 * Math.pow(2, i))); // 300ms, 600ms, 1200ms
                }
            }
            if (last) throw last;
        };

        try {
            let response = await attemptWithRetry(3);

            // Handle 401 with coordinated refresh and single retry
            if (response.status === 401) {
                await this._ensureRefreshed();
                const retry = await attemptWithRetry(2);
                if (retry.ok) return await retry.json();
                if (retry.status === 401) throw new Error('Authentication required');
                if (retry.status === 404) throw new Error('Resource not found');
                if (retry.status === 402) throw new Error('Active subscription required');
                throw new Error(`API Error: ${retry.status} ${retry.statusText}`);
            }

            if (!response.ok) {
                if (response.status === 402) throw new Error('Active subscription required');
                if (response.status === 404) throw new Error('Resource not found');
                throw new Error(`API Error: ${response.status} ${response.statusText}`);
            }
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('API Request Error:', error);
            throw error;
        }
    }

    // Coordinate refresh calls to avoid stampede
    async _ensureRefreshed() {
        if (this._auth && typeof this._auth.silentRefresh === 'function') {
            return await this._auth.silentRefresh();
        }
        if (this._refreshInFlight) return this._refreshInFlight;
        this._refreshInFlight = (async () => {
            try {
                let r = await fetch(`${this.baseUrl}/api/auth/refresh`, { method: 'POST', credentials: 'include' });
                if (!r.ok && r.status === 404) {
                    r = await fetch(`${this.baseUrl}/auth/refresh`, { method: 'POST', credentials: 'include' });
                }
                if (!r.ok) throw new Error('refresh_failed');
                await r.json().catch(()=>({}));
            } finally {
                this._refreshInFlight = null;
            }
        })();
        return this._refreshInFlight;
    }

    // Clear authentication (UI-only state)
    clearAuth() {
        // Do not store tokens; clear any legacy keys for safety
        localStorage.removeItem('access_token');
        localStorage.removeItem('auth_token');
        localStorage.removeItem('token');
        localStorage.removeItem('a3e_api_key');
        sessionStorage.removeItem('access_token');
        sessionStorage.removeItem('auth_token');
    }

    // ===============
    // AUTH HELPERS
    // ===============
    async me() {
        if (this._auth && typeof this._auth.me === 'function') return await this._auth.me();
        try {
            const r = await fetch(`${this.baseUrl}/api/auth/me`, { credentials: 'include' });
            if (r.ok) return await r.json();
        } catch (_) {}
        return { ok: false };
    }

    async logout() {
        if (this._auth && typeof this._auth.logout === 'function') return await this._auth.logout();
        try {
            const r = await fetch(`${this.baseUrl}/api/auth/logout`, { method: 'POST', credentials: 'include' });
            if (r.ok) return await r.json();
        } catch (_) {}
        return { success: false };
    }

    // ===============================
    // ORGANIZATION CHART API METHODS
    // ===============================

    // Simple endpoints (intelligence-simple)
    async saveOrgChartSimple(chartData) {
        const payload = {
            name: chartData.name,
            description: chartData.description,
            nodes: chartData.nodes || [],
            edges: chartData.edges || [],
            metadata: chartData.metadata || {}
        };
        try {
            return await this.request('/api/user/intelligence-simple/org-chart/save', {
                method: 'POST',
                body: JSON.stringify(payload)
            });
        } catch (e) {
            if ((e && e.message && e.message.includes('Resource not found')) || (e && e.message && e.message.includes('404'))) {
                return await this.request('/api/user/intelligence-simple/org-chart', {
                    method: 'POST',
                    body: JSON.stringify(payload)
                });
            }
            throw e;
        }
    }

    async loadOrgChartSimple() {
        try {
            return await this.request('/api/user/intelligence-simple/org-chart/load');
        } catch (e) {
            if ((e && e.message && e.message.includes('Resource not found')) || (e && e.message && e.message.includes('404'))) {
                return await this.request('/api/user/intelligence-simple/org-chart');
            }
            throw e;
        }
    }

    // Create new organization chart
    async createOrgChart(chartData) {
        return await this.request('/api/v1/org-chart', {
            method: 'POST',
            body: JSON.stringify({
                name: chartData.name || 'My Organization Chart',
                description: chartData.description || '',
                data: {
                    nodes: chartData.nodes || [],
                    edges: chartData.edges || [],
                    metadata: chartData.metadata || {}
                },
                institution_type: chartData.institution_type,
                total_employees: chartData.total_employees
            })
        });
    }

    // Get all organization charts for user
    async getOrgCharts() {
        return await this.request('/api/v1/org-chart');
    }

    // Get specific organization chart
    async getOrgChart(chartId) {
        return await this.request(`/api/v1/org-chart/${chartId}`);
    }

    // Update organization chart
    async updateOrgChart(chartId, chartData) {
        return await this.request(`/api/v1/org-chart/${chartId}`, {
            method: 'PUT',
            body: JSON.stringify({
                name: chartData.name,
                description: chartData.description,
                data: {
                    nodes: chartData.nodes || [],
                    edges: chartData.edges || [],
                    metadata: chartData.metadata || {}
                },
                institution_type: chartData.institution_type,
                total_employees: chartData.total_employees
            })
        });
    }

    // Delete organization chart
    async deleteOrgChart(chartId) {
        return await this.request(`/api/v1/org-chart/${chartId}`, {
            method: 'DELETE'
        });
    }

    // Analyze organization chart for compliance
    async analyzeOrgChart(chartId) {
        return await this.request(`/api/v1/org-chart/${chartId}/analyze`, {
            method: 'POST'
        });
    }

    // ===============================
    // SCENARIOS API METHODS  
    // ===============================

    // Calculate ROI scenario
    async calculateScenario(inputs) {
        return await this.request('/api/v1/scenarios/calculate', {
            method: 'POST',
            body: JSON.stringify({ inputs })
        });
    }

    // Save scenario
    async saveScenario(scenarioData) {
        return await this.request('/api/v1/scenarios', {
            method: 'POST',
            body: JSON.stringify({
                name: scenarioData.name || 'My Scenario',
                description: scenarioData.description || '',
                inputs: scenarioData.inputs,
                is_template: scenarioData.is_template || false
            })
        });
    }

    // Get all scenarios for user
    async getScenarios(includeTemplates = true) {
        return await this.request(`/api/v1/scenarios?include_templates=${includeTemplates}`);
    }

    // Get specific scenario
    async getScenario(scenarioId) {
        return await this.request(`/api/v1/scenarios/${scenarioId}`);
    }

    // Delete scenario
    async deleteScenario(scenarioId) {
        return await this.request(`/api/v1/scenarios/${scenarioId}`, {
            method: 'DELETE'
        });
    }

    // Get scenario templates
    async getScenarioTemplates() {
        return await this.request('/api/v1/scenarios/templates', {
            auth: false // Templates are public
        });
    }

    // ===============================
    // POWERBI API METHODS
    // ===============================

    // Get Power BI configuration and status
    async getPowerBIConfig() {
        return await this.request('/api/v1/powerbi/config');
    }

    // Get available reports
    async getPowerBIReports() {
        return await this.request('/api/v1/powerbi/reports');
    }

    // Create Power BI embed token
    async createEmbedToken(config) {
        return await this.request('/api/v1/powerbi/embed-token', {
            method: 'POST',
            body: JSON.stringify({
                report_ids: config.report_ids || [],
                dataset_ids: config.dataset_ids || [],
                username: config.username,
                roles: config.roles || ['User'],
                filters: config.filters || {}
            })
        });
    }

    // Get available datasets
    async getDatasets() {
        return await this.request('/api/v1/powerbi/datasets');
    }

    // Refresh a dataset
    async refreshDataset(datasetId, notifyOption = 'MailOnCompletion') {
        return await this.request(`/api/v1/powerbi/refresh/${datasetId}?notify_option=${notifyOption}`, {
            method: 'POST'
        });
    }

    // Get refresh history for a dataset
    async getRefreshHistory(datasetId, top = 10) {
        return await this.request(`/api/v1/powerbi/refresh/${datasetId}/history?top=${top}`);
    }

    // Configure Row-Level Security
    async configureRLS(institutionFilter) {
        return await this.request('/api/v1/powerbi/row-level-security', {
            method: 'POST',
            body: JSON.stringify({ institution_filter: institutionFilter })
        });
    }

    // ===============================
    // UTILITY METHODS
    // ===============================

    // Test API connection
    async testConnection() {
        try {
            const response = await fetch(`${this.baseUrl}/health`);
            return response.ok;
        } catch (error) {
            return false;
        }
    }

    // Show user-friendly error messages
    showError(error, containerId = 'error-container') {
        const container = document.getElementById(containerId);
        if (container) {
            container.innerHTML = `
                <div class="bg-red-50 border border-red-200 rounded-md p-4 mb-4">
                    <div class="flex">
                        <div class="ml-3">
                            <h3 class="text-sm font-medium text-red-800">Error</h3>
                            <div class="mt-2 text-sm text-red-700">${error.message}</div>
                        </div>
                    </div>
                </div>
            `;
        } else {
            alert(`Error: ${error.message}`);
        }
    }

    // Show success messages
    showSuccess(message, containerId = 'success-container') {
        const container = document.getElementById(containerId);
        if (container) {
            container.innerHTML = `
                <div class="bg-green-50 border border-green-200 rounded-md p-4 mb-4">
                    <div class="flex">
                        <div class="ml-3">
                            <h3 class="text-sm font-medium text-green-800">Success</h3>
                            <div class="mt-2 text-sm text-green-700">${message}</div>
                        </div>
                    </div>
                </div>
            `;
            
            // Auto-hide after 3 seconds
            setTimeout(() => {
                container.innerHTML = '';
            }, 3000);
        }
    }
}

// Create global API instance
window.mmsAPI = new MapMyStandardsAPI();

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { MapMyStandardsAPI, API_CONFIG };
}
