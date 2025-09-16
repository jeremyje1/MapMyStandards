/**
 * API Configuration for MapMyStandards Platform
 * Frontend Integration for Phase K
 */

// Configuration object for different environments
const API_CONFIG = {
    development: {
        baseUrl: 'http://localhost:8000',
        domain: 'localhost:8000'
    },
    production: {
        baseUrl: 'https://api.mapmystandards.ai',
        domain: 'api.mapmystandards.ai'
    }
};

// Detect environment (you can also use environment variables)
const isProduction = (
    window.location.hostname === 'platform.mapmystandards.ai' ||
    window.location.hostname === 'www.mapmystandards.ai' ||
    window.location.hostname.endsWith('.vercel.app')
);

// Current configuration
const config = isProduction ? API_CONFIG.production : API_CONFIG.development;

/**
 * API Client for MapMyStandards Backend
 */
class MapMyStandardsAPI {
    constructor() {
        this.baseUrl = config.baseUrl;
        this.authToken = this.getAuthToken();
        this.cookieAuth = true; // leverage HttpOnly cookies if present
    }

    // Get authentication token from storage (check multiple keys for compatibility)
    getAuthToken() {
        return localStorage.getItem('access_token') || 
               localStorage.getItem('auth_token') || 
               localStorage.getItem('token') ||
               localStorage.getItem('a3e_api_key') ||
               sessionStorage.getItem('access_token') ||
               sessionStorage.getItem('auth_token');
    }

    // Set authentication token
    setAuthToken(token) {
        // Store with multiple keys for compatibility
        localStorage.setItem('access_token', token);
        localStorage.setItem('auth_token', token);
        localStorage.setItem('token', token);
        this.authToken = token;
    }

    // Common headers for API requests
    getHeaders(includeAuth = true) {
        const headers = {
            'Content-Type': 'application/json'
        };
        
        if (includeAuth && this.authToken) {
            headers['Authorization'] = `Bearer ${this.authToken}`;
        }
        
        return headers;
    }

    // Generic API request method
    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const defaultOptions = {
            headers: this.getHeaders(options.auth !== false),
            credentials: 'include',
            ...options
        };

        const backoffOnce = async () => {
            let delay = 500;
            try {
                return await fetch(url, defaultOptions);
            } catch (e) {
                await new Promise(r=>setTimeout(r, delay));
                return await fetch(url, defaultOptions);
            }
        };

        try {
            let response = await fetch(url, defaultOptions);
            if ((response.status >= 500 && response.status <= 504) || response.status === 0) {
                await new Promise(r=>setTimeout(r, 500));
                response = await backoffOnce();
            }
            
            if (!response.ok) {
                if (response.status === 401) {
                    // Try silent refresh if cookies available
                    try {
                        // Prefer session auth refresh first
                        let r = await fetch(`${this.baseUrl}/api/auth/refresh`, { method: 'POST', credentials: 'include' });
                        if (!r.ok && r.status === 404) {
                            // Fallback to enhanced auth refresh
                            r = await fetch(`${this.baseUrl}/auth/refresh`, { method: 'POST', credentials: 'include' });
                        }
                        if (r.ok) {
                            const j = await r.json().catch(()=>({}));
                            if (j && j.access_token) {
                                this.setAuthToken(j.access_token);
                            }
                            // retry original request once
                            const retry = await fetch(url, { ...defaultOptions, headers: this.getHeaders(options.auth !== false) });
                            if (retry.ok) return await retry.json();
                        }
                    } catch (_) {}
                    this.clearAuth();
                    throw new Error('Authentication required');
                }
                if (response.status === 402) {
                    throw new Error('Active subscription required');
                }
                if (response.status === 404) {
                    throw new Error('Resource not found');
                }
                throw new Error(`API Error: ${response.status} ${response.statusText}`);
            }
            
            const data = await response.json();
            return data;
        } catch (error) {
            console.error('API Request Error:', error);
            throw error;
        }
    }

    // Clear authentication
    clearAuth() {
        // Clear all possible token keys
        localStorage.removeItem('access_token');
        localStorage.removeItem('auth_token');
        localStorage.removeItem('token');
        localStorage.removeItem('a3e_api_key');
        sessionStorage.removeItem('access_token');
        sessionStorage.removeItem('auth_token');
        this.authToken = null;
    }

    // ===============================
    // ORGANIZATION CHART API METHODS
    // ===============================

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
