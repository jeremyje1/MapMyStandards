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
  // Auth endpoints
  auth: {
    login: (email: string, password: string) =>
      api.post('/auth/login', { email, password }),
    
    register: (data: { email: string; password: string; name: string; institutionName?: string }) =>
      api.post('/auth/register', data),
    
    logout: () => {
      setAuthToken(null);
      localStorage.removeItem('refreshToken');
      return Promise.resolve();
    },
    
    getCurrentUser: () =>
      api.get('/auth/me'),
    
    sendMagicLink: (email: string) =>
      api.post('/auth/magic-link', { email }),
    
    verifyMagicLink: (token: string) =>
      api.post('/auth/verify-magic-link', { token }),
    
    resetPassword: (email: string) =>
      api.post('/auth/reset-password', { email }),
    
    updatePassword: (token: string, newPassword: string) =>
      api.post('/auth/update-password', { token, newPassword }),
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
  },
  
  // Billing endpoints
  billing: {
    getPlans: () =>
      api.get('/api/v1/billing/plans'),
    
    getCurrentSubscription: () =>
      api.get('/api/v1/billing/subscription'),
    
    createCheckoutSession: (planId: string) =>
      api.post('/api/v1/billing/create-checkout-session', { planId }),
    
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
      api.get('/dashboard/overview'),
    
    getMetrics: () =>
      api.get('/dashboard/metrics'),
    
    getRecentActivity: () =>
      api.get('/dashboard/activity'),
    
    getComplianceStatus: () =>
      api.get('/dashboard/compliance'),
  },
  
  // Health check
  health: () =>
    api.get('/health'),
};

export default apiService;