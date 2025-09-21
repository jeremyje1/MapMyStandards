import axios, { AxiosInstance, AxiosError } from 'axios';

// API base URL - use environment variable or fallback to production
const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://api.mapmystandards.ai';

// Create axios instance with default config
const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Important for CORS with credentials
});

// Token management
export const setAuthToken = (token: string | null) => {
  if (token) {
    api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    localStorage.setItem('token', token);
  } else {
    delete api.defaults.headers.common['Authorization'];
    localStorage.removeItem('token');
  }
};

// Initialize token from localStorage
const storedToken = localStorage.getItem('token');
if (storedToken) {
  setAuthToken(storedToken);
}

// Request interceptor for adding token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for handling errors
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as any;
    
    // Handle 401 Unauthorized
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      // Try to refresh token
      try {
        const refreshToken = localStorage.getItem('refreshToken');
        if (refreshToken) {
          const response = await api.post('/auth/refresh', { refreshToken });
          const { token } = response.data;
          setAuthToken(token);
          return api(originalRequest);
        }
      } catch (refreshError) {
        // Refresh failed, redirect to login
        setAuthToken(null);
        localStorage.removeItem('refreshToken');
        window.location.href = '/login';
      }
    }
    
    return Promise.reject(error);
  }
);

// API service methods
const apiService = {
  // raw helper for custom calls when needed
  raw: api,
  // Uploads (DB-backed)
  uploads: {
    upload: (file: File, opts?: { title?: string; description?: string; accreditor?: string }) => {
      const form = new FormData();
      form.append('file', file);
      if (opts?.title) form.append('title', opts.title);
      if (opts?.description) form.append('description', opts.description);
      if (opts?.accreditor) form.append('accreditor', opts.accreditor);
      return api.post('/api/uploads', form, { headers: { 'Content-Type': 'multipart/form-data' } });
    },
    getJob: (jobId: string) => api.get(`/api/uploads/jobs/${jobId}`),
    recent: (limit = 10) => api.get('/api/uploads/recent', { params: { limit } })
  },
  // Auth endpoints
  auth: {
    // Session-based login against production API
    login: async (email: string, password: string) => {
      return api.post('/api/auth/login', { email, password, rememberMe: false });
    },

    register: (data: { 
      email: string; 
      password: string; 
      first_name: string; 
      last_name: string; 
      institution_name: string;
      plan: string;
      billing_period: string;
      is_trial: boolean;
    }) =>
      api.post('/api/auth/register', data),
    
    completeRegistration: (data: { session_id: string; email: string; password: string }) =>
      api.post('/api/auth/complete-registration', data),
    
    logout: () => {
      setAuthToken(null);
      localStorage.removeItem('refreshToken');
      return api.post('/api/auth/logout');
    },
    
    getCurrentUser: () =>
      api.get('/api/auth/me'),
    
    // Not available in production backend; keep as stub with clear error
    sendMagicLink: async (_email: string) => {
      throw new Error('Magic link sign-in is not enabled on this environment.');
    },
    
    verifyMagicLink: async (_token: string) => {
      throw new Error('Magic link verification is not enabled on this environment.');
    },
    
    resetPassword: async (_email: string) => {
      throw new Error('Password reset is not enabled on this environment.');
    },
    
    updatePassword: async (_token: string, _newPassword: string) => {
      throw new Error('Password reset is not enabled on this environment.');
    },
  },
  
  // User endpoints
  users: {
    getProfile: () =>
      api.get('/users/profile'),
    
    updateProfile: (data: any) =>
      api.put('/users/profile', data),
    
    uploadAvatar: (file: File) => {
      const formData = new FormData();
      formData.append('avatar', file);
      return api.post('/users/avatar', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
    },
  },
  
  // Institution endpoints
  institutions: {
    get: () =>
      api.get('/institutions'),
    
    update: (data: any) =>
      api.put('/institutions', data),
    
    getUsers: () =>
      api.get('/institutions/users'),
    
    inviteUser: (email: string, role: string) =>
      api.post('/institutions/invite', { email, role }),
  },
  
  // Document endpoints
  documents: {
    list: (params?: { page?: number; limit?: number; search?: string }) =>
      api.get('/documents', { params }),
    
    upload: (file: File, metadata?: any) => {
      const formData = new FormData();
      formData.append('file', file);
      if (metadata) {
        formData.append('metadata', JSON.stringify(metadata));
      }
      return api.post('/documents/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
    },
    
    get: (id: string) =>
      api.get(`/documents/${id}`),
    
    delete: (id: string) =>
      api.delete(`/documents/${id}`),
    
    process: (id: string) =>
      api.post(`/documents/${id}/process`),
  },
  
  // Reports endpoints
  reports: {
    list: () =>
      api.get('/reports'),
    
    generate: (type: string, params?: any) =>
      api.post('/reports/generate', { type, ...params }),
    
    get: (id: string) =>
      api.get(`/reports/${id}`),
    
    download: (id: string) =>
      api.get(`/reports/${id}/download`, { responseType: 'blob' }),
  },
  
  // Intelligence Simple endpoints
  intelligenceSimple: {
    // Evidence reviews list (review queue)
    listReviews: (params?: { status?: string; limit?: number }) =>
      api.get('/api/user/intelligence-simple/evidence/reviews', { params }),

    // Readiness scorecard snapshot
    readinessScorecard: (params?: { accreditor?: string }) =>
      api.get('/api/user/intelligence-simple/readiness/scorecard', { params }),

    // Risk aggregate summary
    riskAggregate: (params?: { accreditor?: string }) =>
      api.get('/api/user/intelligence-simple/risk/aggregate', { params }),

    // Metrics timeseries (coverage trend)
    metricsTimeseries: (params?: { accreditor?: string }) =>
      api.get('/api/user/intelligence-simple/metrics/timeseries', { params }),
  },
  
  // Standards endpoints
  standards: {
    list: () =>
      api.get('/standards'),
    
    getByAccreditor: (accreditor: string) =>
      api.get(`/standards/${accreditor}`),
    
    getMappings: () =>
      api.get('/standards/mappings'),
    
    updateMapping: (standardId: string, documentId: string, confidence: number) =>
      api.post('/standards/mappings', { standardId, documentId, confidence }),

    // Checklist and stats (live endpoints)
    getChecklist: async (params?: { accreditor?: string; format?: 'json'|'csv'; include_indicators?: boolean }) => {
      return api.get('/api/user/intelligence-simple/standards/checklist', { params });
    },

    getChecklistStats: async (params?: { accreditor?: string; include_indicators?: boolean }) => {
      return api.get('/api/user/intelligence-simple/standards/checklist/stats', { params });
    },

    // Reviewer pack export
    exportReviewerPack: (payload: { standard_ids: string[]; include_files?: boolean; include_checklist?: boolean; include_metrics?: boolean; checklist_format?: 'json'|'csv'; accreditor?: string; body?: string; }) =>
      api.post('/api/user/intelligence-simple/narratives/export/reviewer-pack', payload, { responseType: 'json' }),
  },
  
  // Billing endpoints
  billing: {
    getPlans: () =>
      api.get('/api/v1/billing/plans'),
    
    getCurrentSubscription: () =>
      api.get('/api/v1/billing/subscription'),
    
    createCheckoutSession: (priceId: string) =>
      api.post('/api/v1/billing/create-checkout-session', {
        price_id: priceId,
        success_url: `${window.location.origin}/checkout/success?session_id={CHECKOUT_SESSION_ID}`,
        cancel_url: `${window.location.origin}/pricing`,
        customer_email: null,
        metadata: {},
        trial_period_days: 14
      }),
    
    verifyCheckoutSession: (sessionId: string) =>
      api.get(`/api/v1/billing/verify-session/${sessionId}`),
    
    cancelSubscription: () =>
      api.post('/api/v1/billing/cancel-subscription'),
    
    getBillingHistory: () =>
      api.get('/api/v1/billing/history'),
    
    updatePaymentMethod: (paymentMethodId: string) =>
      api.post('/api/v1/billing/update-payment-method', { paymentMethodId }),
  },
  
  // Dashboard endpoints
  dashboard: {
    getOverview: () =>
      api.get('/api/dashboard/overview'),
    
    getMetrics: () =>
      api.get('/api/metrics/dashboard'),
    
    getRecentActivity: () =>
      api.get('/api/dashboard/notifications'),
    
    getComplianceStatus: () =>
      api.get('/api/dashboard/analytics'),
  },
  
  // Health check
  health: () =>
    api.get('/health'),
};

export default apiService;