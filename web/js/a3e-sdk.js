/**
 * A³E JavaScript SDK
 * Client library for integrating with the A³E API
 * 
 * Usage:
 * const a3e = new A3EClient({
 *   apiKey: 'your-api-key',
 *   baseURL: 'https://api.mapmystandards.ai'
 * });
 */

class A3EClient {
    constructor(config) {
        this.apiKey = config.apiKey;
        this.baseURL = config.baseURL || 'https://api.mapmystandards.ai';
        this.version = 'v1';
    }

    /**
     * Make authenticated API request
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}/api/${this.version}${endpoint}`;
        
        const config = {
            headers: {
                'Content-Type': 'application/json',
                'X-API-Key': this.apiKey,
                ...options.headers
            },
            ...options
        };

        if (options.body && typeof options.body === 'object') {
            config.body = JSON.stringify(options.body);
        }

        try {
            const response = await fetch(url, config);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || `HTTP ${response.status}`);
            }

            return data;
        } catch (error) {
            console.error('A³E API Error:', error);
            throw error;
        }
    }

    /**
     * Health check
     */
    async health() {
        return this.request('/health');
    }

    /**
     * Get account status and usage
     */
    async getAccountStatus() {
        return this.request('/billing/account/status');
    }

    // === Document Analysis ===

    /**
     * Analyze a document for accreditation compliance
     */
    async analyzeDocument(file, options = {}) {
        const formData = new FormData();
        formData.append('file', file);
        
        if (options.accreditor) {
            formData.append('accreditor', options.accreditor);
        }
        
        if (options.institution_type) {
            formData.append('institution_type', options.institution_type);
        }

        return this.request('/documents/analyze', {
            method: 'POST',
            body: formData,
            headers: {
                // Remove Content-Type to let browser set boundary
                'X-API-Key': this.apiKey
            }
        });
    }

    /**
     * Analyze evidence for specific standards
     */
    async analyzeEvidence(text, standards = []) {
        return this.request('/proprietary/analyze/evidence', {
            method: 'POST',
            body: {
                text: text,
                standards: standards
            }
        });
    }

    // === Standards Management ===

    /**
     * Get all supported accreditors
     */
    async getAccreditors() {
        return this.request('/standards/accreditors');
    }

    /**
     * Search standards by query
     */
    async searchStandards(query, accreditor = null) {
        const params = new URLSearchParams({ query });
        if (accreditor) params.append('accreditor', accreditor);
        
        return this.request(`/standards/search?${params}`);
    }

    /**
     * Get standards for specific accreditor
     */
    async getStandardsByAccreditor(accreditor) {
        return this.request(`/standards/accreditor/${accreditor}`);
    }

    // === Proprietary AI Features ===

    /**
     * Get ontology concepts
     */
    async getOntologyConcepts() {
        return this.request('/proprietary/ontology/concepts');
    }

    /**
     * Get ontology insights for text
     */
    async getOntologyInsights(text) {
        return this.request('/proprietary/ontology/insights', {
            method: 'POST',
            body: { text: text }
        });
    }

    /**
     * Run multi-agent analysis pipeline
     */
    async runMultiAgentAnalysis(text, context = {}) {
        return this.request('/proprietary/agents/analyze', {
            method: 'POST',
            body: {
                text: text,
                context: context
            }
        });
    }

    /**
     * Get vector matching results
     */
    async getVectorMatches(query, threshold = 0.75) {
        return this.request('/proprietary/vector/match', {
            method: 'POST',
            body: {
                query: query,
                threshold: threshold
            }
        });
    }

    /**
     * Get audit trail for analysis
     */
    async getAuditTrail(analysisId) {
        return this.request(`/proprietary/audit/${analysisId}`);
    }

    // === Integrations ===

    /**
     * Get Canvas courses
     */
    async getCanvasCourses() {
        return this.request('/integrations/canvas/courses');
    }

    /**
     * Get Canvas course documents
     */
    async getCanvasCourseDocuments(courseId) {
        return this.request(`/integrations/canvas/courses/${courseId}/documents`);
    }

    // === Billing & Subscription ===

    /**
     * Get pricing plans
     */
    async getPricingPlans() {
        return this.request('/billing/plans');
    }

    /**
     * Create subscription
     */
    async createSubscription(customerId, plan, paymentMethodId) {
        return this.request('/billing/subscription/create', {
            method: 'POST',
            body: {
                customer_id: customerId,
                plan: plan,
                payment_method_id: paymentMethodId
            }
        });
    }

    /**
     * Cancel subscription
     */
    async cancelSubscription(customerId) {
        return this.request('/billing/subscription/cancel', {
            method: 'POST',
            body: { customer_id: customerId }
        });
    }
}

/**
 * A³E Web Components
 * Ready-to-use UI components for common workflows
 */

class A3EComponents {
    constructor(client) {
        this.client = client;
    }

    /**
     * Create document upload component
     */
    createUploadComponent(containerId, options = {}) {
        const container = document.getElementById(containerId);
        
        container.innerHTML = `
            <div class="a3e-upload-component">
                <div class="upload-area" ondrop="drop(event)" ondragover="allowDrop(event)">
                    <input type="file" id="fileInput" accept=".pdf,.doc,.docx" multiple>
                    <label for="fileInput" class="upload-label">
                        <svg class="upload-icon" viewBox="0 0 24 24">
                            <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z"/>
                        </svg>
                        <span>Drop files here or click to upload</span>
                    </label>
                </div>
                <div class="upload-progress" style="display: none;">
                    <div class="progress-bar"></div>
                    <span class="progress-text">Analyzing...</span>
                </div>
                <div class="upload-results"></div>
            </div>
        `;

        // Add event listeners
        const fileInput = container.querySelector('#fileInput');
        const progressDiv = container.querySelector('.upload-progress');
        const resultsDiv = container.querySelector('.upload-results');

        fileInput.addEventListener('change', async (e) => {
            const files = Array.from(e.target.files);
            await this.processFiles(files, progressDiv, resultsDiv, options);
        });
    }

    /**
     * Process uploaded files
     */
    async processFiles(files, progressDiv, resultsDiv, options) {
        progressDiv.style.display = 'block';
        resultsDiv.innerHTML = '';

        for (const file of files) {
            try {
                const result = await this.client.analyzeDocument(file, options);
                this.displayResult(result, resultsDiv);
            } catch (error) {
                this.displayError(error, resultsDiv);
            }
        }

        progressDiv.style.display = 'none';
    }

    /**
     * Display analysis result
     */
    displayResult(result, container) {
        const resultDiv = document.createElement('div');
        resultDiv.className = 'analysis-result';
        resultDiv.innerHTML = `
            <h3>${result.document_name}</h3>
            <p>Quality Score: ${result.quality_score}/10</p>
            <p>Mapped Standards: ${result.mapped_standards?.length || 0}</p>
            <div class="standards-list">
                ${result.mapped_standards?.map(s => `<span class="standard-tag">${s.code}</span>`).join('') || ''}
            </div>
        `;
        container.appendChild(resultDiv);
    }

    /**
     * Display error
     */
    displayError(error, container) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'analysis-error';
        errorDiv.innerHTML = `<p>Error: ${error.message}</p>`;
        container.appendChild(errorDiv);
    }
}

// Export for different module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { A3EClient, A3EComponents };
}

if (typeof window !== 'undefined') {
    window.A3EClient = A3EClient;
    window.A3EComponents = A3EComponents;
}

// CSS for components
const css = `
.a3e-upload-component {
    max-width: 600px;
    margin: 0 auto;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.upload-area {
    border: 2px dashed #ccc;
    border-radius: 8px;
    padding: 40px;
    text-align: center;
    cursor: pointer;
    transition: border-color 0.3s;
}

.upload-area:hover {
    border-color: #007bff;
}

.upload-label {
    display: flex;
    flex-direction: column;
    align-items: center;
    cursor: pointer;
}

.upload-icon {
    width: 48px;
    height: 48px;
    margin-bottom: 16px;
    fill: #6c757d;
}

.upload-progress {
    margin: 20px 0;
    text-align: center;
}

.progress-bar {
    width: 100%;
    height: 8px;
    background: #e9ecef;
    border-radius: 4px;
    overflow: hidden;
}

.progress-bar::after {
    content: '';
    display: block;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, #007bff, #0056b3);
    animation: progress 2s infinite;
}

@keyframes progress {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(100%); }
}

.analysis-result {
    border: 1px solid #dee2e6;
    border-radius: 8px;
    padding: 16px;
    margin: 16px 0;
    background: #f8f9fa;
}

.standard-tag {
    display: inline-block;
    background: #007bff;
    color: white;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 12px;
    margin: 2px;
}

.analysis-error {
    border: 1px solid #dc3545;
    border-radius: 8px;
    padding: 16px;
    margin: 16px 0;
    background: #f8d7da;
    color: #721c24;
}
`;

// Inject CSS
if (typeof document !== 'undefined') {
    const style = document.createElement('style');
    style.textContent = css;
    document.head.appendChild(style);
}
