import React, { createContext, useContext, useState, useEffect } from 'react';
import { User, LoginResponse, DemoRoleItem, DemoRolesResponse } from '../../types';

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  loading: boolean;
  demoRoles: DemoRoleItem[];
  demoMode: boolean;
  loginAsDemo: (roleKey: string) => Promise<void>;
  login: (email: string, password: string) => Promise<void>;
  requestOtp: (email: string, fullName?: string, role?: string) => Promise<{ dev_otp?: string; message: string }>;
  verifyOtp: (email: string, otp: string, fullName?: string, role?: string) => Promise<void>;
  logout: () => void;
  error: string | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('patient360_access_token'));
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [demoRoles, setDemoRoles] = useState<DemoRoleItem[]>([]);
  const [demoMode, setDemoMode] = useState<boolean>(true);

  // Validate existing token and restore user profile
  useEffect(() => {
    const restoreSession = async () => {
      const storedToken = localStorage.getItem('patient360_access_token');
      if (!storedToken) {
        setLoading(false);
        return;
      }

      try {
        const res = await fetch('/api/v1/auth/me', {
          headers: {
            Authorization: `Bearer ${storedToken}`,
          },
        });

        if (res.ok) {
          const profile: User = await res.json();
          setUser(profile);
          setToken(storedToken);
        } else {
          // Token expired or invalid
          localStorage.removeItem('patient360_access_token');
          setToken(null);
          setUser(null);
        }
      } catch (err) {
        console.warn('Could not restore auth session:', err);
      } finally {
        setLoading(false);
      }
    };

    const fetchDemoRoles = async () => {
      try {
        const res = await fetch('/api/v1/auth/demo-roles');
        if (res.ok) {
          const data: DemoRolesResponse = await res.json();
          setDemoMode(data.demo_mode);
          setDemoRoles(data.roles);
        }
      } catch (err) {
        console.warn('Could not fetch demo roles:', err);
      }
    };

    restoreSession();
    fetchDemoRoles();
  }, []);

  const requestOtp = async (email: string, fullName?: string, role?: string): Promise<{ dev_otp?: string; message: string }> => {
    setError(null);
    try {
      const res = await fetch('/api/v1/auth/otp/request', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, full_name: fullName || null, role: role || 'reviewer' }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData?.error?.message || errData?.detail || 'Failed to dispatch verification code.');
      }

      const data = await res.json();
      return { dev_otp: data.dev_otp, message: data.message };
    } catch (err: any) {
      setError(err.message || 'Error requesting verification code');
      throw err;
    }
  };

  const verifyOtp = async (email: string, otp: string, fullName?: string, role?: string): Promise<void> => {
    setError(null);
    try {
      const res = await fetch('/api/v1/auth/otp/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, otp, full_name: fullName || null, role: role || 'reviewer' }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData?.error?.message || errData?.detail || 'Verification failed. Please check the code.');
      }

      const data: LoginResponse = await res.json();
      localStorage.setItem('patient360_access_token', data.access_token);
      setToken(data.access_token);
      setUser(data.user);
    } catch (err: any) {
      setError(err.message || 'Verification failed');
      throw err;
    }
  };

  const login = async (email: string, password: string) => {
    setError(null);
    try {
      const res = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData?.error?.message || 'Authentication failed. Please verify credentials.');
      }

      const data: LoginResponse = await res.json();
      localStorage.setItem('patient360_access_token', data.access_token);
      setToken(data.access_token);
      setUser(data.user);
    } catch (err: any) {
      setError(err.message || 'Login failed');
      throw err;
    }
  };

  const loginAsDemo = async (roleKey: string): Promise<void> => {
    setError(null);
    let attempts = 0;
    const maxAttempts = 2;

    while (attempts < maxAttempts) {
      attempts++;
      try {
        const res = await fetch('/api/v1/auth/demo-login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ role_key: roleKey }),
        });

        if (res.status === 502 || res.status === 504) {
          if (attempts < maxAttempts) {
            // Free-tier cloud server is spinning up from cold sleep; wait 3s and retry
            await new Promise((resolve) => setTimeout(resolve, 3000));
            continue;
          }
          throw new Error('Cloud service is waking up from free-tier sleep. Please try once more in a few seconds.');
        }

        if (!res.ok) {
          const errData = await res.json().catch(() => ({}));
          throw new Error(errData?.detail || errData?.error?.message || 'Demo authentication failed.');
        }

        const data: LoginResponse = await res.json();
        localStorage.setItem('patient360_access_token', data.access_token);
        setToken(data.access_token);
        setUser(data.user);
        return;
      } catch (err: any) {
        if (attempts >= maxAttempts) {
          setError(err.message || 'Demo login failed');
          throw err;
        }
        await new Promise((resolve) => setTimeout(resolve, 2000));
      }
    }
  };

  const logout = () => {
    localStorage.removeItem('patient360_access_token');
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!user,
        loading,
        demoRoles,
        demoMode,
        loginAsDemo,
        login,
        requestOtp,
        verifyOtp,
        logout,
        error,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
