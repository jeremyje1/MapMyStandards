import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import api, { setAuthToken } from '../services/api';

interface User {
  id: string;
  email: string;
  name: string;
  role?: string;
  plan?: string;
  institutionId?: string;
  institutionName?: string;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, firstName: string, lastName: string, institutionName?: string) => Promise<void>;
  logout: () => void;
  sendMagicLink: (email: string) => Promise<void>;
  verifyMagicLink: (token: string) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  // Check if user is logged in on mount (session cookie)
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const response = await api.auth.getCurrentUser();
        // Expect shape like { ok: true, user: { ... } } or similar
        const d: any = response.data || {};
        if (d && (d.user || d.ok)) {
          const u = d.user || { id: d.user_id, email: d.email, name: d.name };
          if (u && u.email) setUser(u);
        }
      } catch (error) {
        // Not logged in; ignore
      }
      setLoading(false);
    };
    
    checkAuth();
  }, []);

  const login = async (email: string, password: string) => {
    try {
      await api.auth.login(email, password); // sets session cookie
      const me = await api.auth.getCurrentUser();
      const d: any = me.data || {};
      const u = d.user || { id: d.user_id, email: d.email, name: d.name };
      if (!u || !u.email) throw new Error('Login failed');
      setUser(u);
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Login failed');
    }
  };

  const register = async (email: string, password: string, firstName: string, lastName: string, institutionName?: string) => {
    try {
      const response = await api.auth.register({ 
        email, 
        password, 
        first_name: firstName,
        last_name: lastName,
        institution_name: institutionName || '',
        plan: 'professional',
        billing_period: 'monthly',
        is_trial: true
      });
      
      // Backend returns data.access_token, not data.token
      const { access_token, user } = response.data.data;
      
      setAuthToken(access_token);
      setUser(user);
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Registration failed');
    }
  };

  const logout = () => {
    api.auth.logout();
    setUser(null);
    setAuthToken(null);
    window.location.href = '/login';
  };

  const sendMagicLink = async (_email: string) => {
    throw new Error('Magic link sign-in is not enabled on this environment.');
  };

  const verifyMagicLink = async (_token: string) => {
    throw new Error('Magic link verification is not enabled on this environment.');
  };

  const value = {
    user,
    loading,
    login,
    register,
    logout,
    sendMagicLink,
    verifyMagicLink,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};