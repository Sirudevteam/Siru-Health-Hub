'use client';

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { getApiBase } from '@/lib/api';

export type UserRole = 'ADMIN' | 'DOCTOR' | 'NURSE' | 'PATIENT';

export interface AuthUser {
  id?: string;
  username: string;
  role: UserRole;
  patient_id?: string | null;
  practitioner_id?: string | null;
  active?: boolean;
}

interface AuthContextType {
  user: AuthUser | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<AuthUser>;
  logout: () => Promise<void>;
  switchDemoUser: (role: UserRole) => Promise<AuthUser>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const TOKEN_KEY = 'siru_access_token';
const USER_KEY = 'siru_auth_user';

export const DEMO_CREDENTIALS: Record<UserRole, { username: string; password: string; title: string; desc: string }> = {
  ADMIN: {
    username: 'admin',
    password: 'admin123',
    title: 'Hospital Administrator',
    desc: 'Full access to HIPAA audit trails, executive analytics, and all patient records.'
  },
  DOCTOR: {
    username: 'doctor.sharma',
    password: 'doctor123',
    title: 'Dr. Rajesh Sharma, MD',
    desc: 'Practitioner PR101: Diagnoses (ICD-10), Prescribes (Rx), and submits claims.'
  },
  NURSE: {
    username: 'nurse.lakshmi',
    password: 'nurse123',
    title: 'Nurse Lakshmi Priya, RN',
    desc: 'Clinical staff: Records bedside vitals and observations (restricted from prescribing).'
  },
  PATIENT: {
    username: 'patient.arun',
    password: 'patient123',
    title: 'Arun Kumar (Patient)',
    desc: 'Patient P1001: Accesses own health records, vitals, coverage, and EOB claims.'
  }
};

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Restore session from localStorage on mount
  useEffect(() => {
    try {
      const savedToken = localStorage.getItem(TOKEN_KEY);
      const savedUserStr = localStorage.getItem(USER_KEY);
      if (savedToken && savedUserStr) {
        setToken(savedToken);
        setUser(JSON.parse(savedUserStr));
      }
    } catch (e) {
      console.warn('Failed to restore auth session from storage', e);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const login = useCallback(async (username: string, password: string): Promise<AuthUser> => {
    setIsLoading(true);
    try {
      const base = getApiBase();
      const res = await fetch(`${base}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });

      if (!res.ok) {
        const errText = await res.text();
        let message = 'Invalid username or password';
        try {
          const errJson = JSON.parse(errText);
          if (errJson.detail) message = errJson.detail;
        } catch {
          // ignore
        }
        throw new Error(message);
      }

      const data = await res.json();
      const authUser: AuthUser = {
        username: data.username,
        role: data.role as UserRole,
        patient_id: data.patient_id,
        practitioner_id: data.practitioner_id,
      };

      setToken(data.access_token);
      setUser(authUser);

      localStorage.setItem(TOKEN_KEY, data.access_token);
      localStorage.setItem(USER_KEY, JSON.stringify(authUser));

      return authUser;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const logout = useCallback(async () => {
    const activeToken = token || (typeof window !== 'undefined' ? localStorage.getItem(TOKEN_KEY) : null);
    if (activeToken) {
      try {
        const base = getApiBase();
        await fetch(`${base}/auth/logout`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${activeToken}`
          }
        });
      } catch (e) {
        console.warn('Redis revocation request error during logout', e);
      }
    }

    setToken(null);
    setUser(null);
    if (typeof window !== 'undefined') {
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(USER_KEY);
    }
  }, [token]);

  const switchDemoUser = useCallback(async (role: UserRole): Promise<AuthUser> => {
    const cred = DEMO_CREDENTIALS[role];
    return await login(cred.username, cred.password);
  }, [login]);

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!user && !!token,
        isLoading,
        login,
        logout,
        switchDemoUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

