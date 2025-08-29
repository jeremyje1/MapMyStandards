import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import api, { setAuthToken } from '../services/api';

interface User {
  id: string;
  email: string;
  name: string;
  role: string;
  institutionId?: string;
  institutionName?: string;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, name: string, institutionName?: string) => Promise<void>;
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

  // Check if user is logged in on mount
  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('token');
      if (token) {
        try {
          const response = await api.auth.getCurrentUser();
          setUser(response.data.user);
        } catch (error) {
          console.error('Auth check failed:', error);
          setAuthToken(null);
        }
      }
      setLoading(false);
    };
    
    checkAuth();
  }, []);

  const login = async (email: string, password: string) => {
    try {
      const response = await api.auth.login(email, password);
      const { token, user, refreshToken } = response.data;
      
      setAuthToken(token);
      if (refreshToken) {
        localStorage.setItem('refreshToken', refreshToken);
      }
      setUser(user);
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Login failed');
    }
  };

  const register = async (email: string, password: string, name: string, institutionName?: string) => {
    try {
      const response = await api.auth.register({ email, password, name, institutionName });
      const { token, user, refreshToken } = response.data;
      
      setAuthToken(token);
      if (refreshToken) {
        localStorage.setItem('refreshToken', refreshToken);
      }
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

  const sendMagicLink = async (email: string) => {
    try {
      await api.auth.sendMagicLink(email);
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Failed to send magic link');
    }
  };

  const verifyMagicLink = async (token: string) => {
    try {
      const response = await api.auth.verifyMagicLink(token);
      const { token: authToken, user, refreshToken } = response.data;
      
      setAuthToken(authToken);
      if (refreshToken) {
        localStorage.setItem('refreshToken', refreshToken);
      }
      setUser(user);
    } catch (error: any) {
      throw new Error(error.response?.data?.message || 'Invalid or expired magic link');
    }
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