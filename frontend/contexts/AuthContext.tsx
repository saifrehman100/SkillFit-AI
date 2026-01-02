'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import { authAPI } from '@/lib/api/auth';
import { UserResponse } from '@/types/api';

interface AuthContextType {
  user: UserResponse | null;
  token: string | null;
  loading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserResponse | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // Load token and user on mount
  useEffect(() => {
    const loadUser = async () => {
      try {
        const storedToken = localStorage.getItem('access_token');
        if (storedToken) {
          setToken(storedToken);
          const response = await authAPI.getCurrentUser();
          setUser(response.data);
        }
      } catch (error) {
        // Token invalid, clear it
        localStorage.removeItem('access_token');
        setToken(null);
      } finally {
        setLoading(false);
      }
    };

    loadUser();
  }, []);

  const login = async (email: string, password: string) => {
    const response = await authAPI.login({ email, password });
    const { access_token } = response.data;

    localStorage.setItem('access_token', access_token);
    setToken(access_token);

    // Fetch user data
    const userResponse = await authAPI.getCurrentUser();
    setUser(userResponse.data);
  };

  const register = async (email: string, password: string) => {
    const response = await authAPI.register({ email, password });
    const userData = response.data;

    // Auto-login after registration
    await login(email, password);
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    setToken(null);
    setUser(null);
  };

  const refreshUser = async () => {
    try {
      const storedToken = localStorage.getItem('access_token');
      if (storedToken) {
        setToken(storedToken);
        const response = await authAPI.getCurrentUser();
        setUser(response.data);
      }
    } catch (error) {
      // Token invalid, clear it
      localStorage.removeItem('access_token');
      setToken(null);
      setUser(null);
      throw error;
    }
  };

  const value = {
    user,
    token,
    loading,
    isAuthenticated: !!user,
    login,
    register,
    logout,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
