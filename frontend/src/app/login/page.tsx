'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Card } from '@/components/ui/Card';
import { useAuth, DEMO_CREDENTIALS, UserRole } from '@/context/AuthContext';
import {
  FiLock,
  FiUser,
  FiEye,
  FiEyeOff,
  FiAlertCircle,
  FiCheckCircle,
  FiShield,
  FiArrowRight,
  FiLogIn
} from 'react-icons/fi';
import {
  FaHeartPulse,
  FaUserDoctor,
  FaUserNurse,
  FaShieldHalved,
  FaHospitalUser
} from 'react-icons/fa6';

export default function LoginPage() {
  const router = useRouter();
  const { login, switchDemoUser, isAuthenticated, user, logout } = useAuth();

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password.trim()) {
      setError('Please enter both username and password.');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const loggedUser = await login(username.trim(), password);
      redirectUser(loggedUser.role, loggedUser.patient_id);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Authentication failed.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuickLogin = async (role: UserRole) => {
    const cred = DEMO_CREDENTIALS[role];
    setUsername(cred.username);
    setPassword(cred.password);
    setIsLoading(true);
    setError(null);

    try {
      const loggedUser = await switchDemoUser(role);
      redirectUser(loggedUser.role, loggedUser.patient_id);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Demo login failed.');
    } finally {
      setIsLoading(false);
    }
  };

  const redirectUser = (role: UserRole, patientId?: string | null) => {
    if (role === 'PATIENT' && patientId) {
      router.push(`/patients/${patientId}`);
    } else if (role === 'ADMIN') {
      router.push('/admin/analytics');
    } else {
      router.push('/patients');
    }
  };

  const personaConfig: Array<{
    role: UserRole;
    icon: React.ComponentType<{ className?: string }>;
    bg: string;
    border: string;
  }> = [
    {
      role: 'ADMIN',
      icon: FaShieldHalved,
      bg: 'bg-purple-50 text-purple-700 hover:bg-purple-100/80',
      border: 'border-purple-200'
    },
    {
      role: 'DOCTOR',
      icon: FaUserDoctor,
      bg: 'bg-emerald-50 text-emerald-700 hover:bg-emerald-100/80',
      border: 'border-emerald-200'
    },
    {
      role: 'NURSE',
      icon: FaUserNurse,
      bg: 'bg-blue-50 text-blue-700 hover:bg-blue-100/80',
      border: 'border-blue-200'
    },
    {
      role: 'PATIENT',
      icon: FaHospitalUser,
      bg: 'bg-amber-50 text-amber-700 hover:bg-amber-100/80',
      border: 'border-amber-200'
    }
  ];

  return (
    <div className="min-h-[calc(100vh-140px)] flex flex-col items-center justify-center py-10 px-4 sm:px-6">
      <div className="max-w-md w-full space-y-6">

        {/* Brand Header */}
        <div className="text-center space-y-2">
          <div className="inline-flex items-center justify-center w-14 h-14 bg-emerald-700 text-white rounded-2xl shadow-lg mb-2">
            <FaHeartPulse className="w-8 h-8" />
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 tracking-tight">
            Sign In to Siru HealthHub
          </h1>
          <p className="text-sm text-gray-500">
            Enterprise HL7® FHIR® R4 Healthcare Interoperability Platform
          </p>
        </div>

        {/* Already logged in banner */}
        {isAuthenticated && user && (
          <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl text-xs text-emerald-900 flex items-center justify-between shadow-sm">
            <div className="flex items-center gap-2">
              <FiCheckCircle className="w-4 h-4 text-emerald-600 flex-shrink-0" />
              <span>
                Currently logged in as <strong className="font-mono">{user.username}</strong> ({user.role})
              </span>
            </div>
            <button
              onClick={() => logout()}
              className="px-2.5 py-1 bg-white hover:bg-emerald-100 text-emerald-800 rounded border border-emerald-300 font-semibold"
            >
              Sign Out
            </button>
          </div>
        )}

        {/* Main Login Card */}
        <Card className="p-6 sm:p-8 shadow-xl border-gray-200">
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg text-xs text-rose-800 flex items-center gap-2">
                <FiAlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <div>
              <label htmlFor="username" className="block text-xs font-semibold text-gray-700 mb-1">
                Username or Email
              </label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400">
                  <FiUser className="w-4 h-4" />
                </span>
                <input
                  id="username"
                  type="text"
                  placeholder="e.g. admin, doctor.sharma"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="w-full border border-gray-300 rounded-lg pl-9 pr-3 py-2.5 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                  required
                />
              </div>
            </div>

            <div>
              <label htmlFor="password" className="block text-xs font-semibold text-gray-700 mb-1">
                Password
              </label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-400">
                  <FiLock className="w-4 h-4" />
                </span>
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full border border-gray-300 rounded-lg pl-9 pr-10 py-2.5 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600"
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <FiEyeOff className="w-4 h-4" /> : <FiEye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full mt-2 py-2.5 px-4 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-sm font-semibold shadow transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {isLoading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  Authenticating...
                </>
              ) : (
                <>
                  <FiLogIn className="w-4 h-4" /> Sign In
                </>
              )}
            </button>
          </form>

          {/* Quick Demo Persona Switcher */}
          <div className="mt-8 pt-6 border-t border-gray-100">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-bold uppercase tracking-wider text-gray-500 flex items-center gap-1.5">
                <FiShield className="w-3.5 h-3.5 text-emerald-600" />
                One-Click Healthcare Demo Personas
              </span>
              <span className="text-[10px] text-gray-400">Click to Auto-Login</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              {personaConfig.map(({ role, icon: PersonaIcon, bg, border }) => {
                const cred = DEMO_CREDENTIALS[role];
                return (
                  <button
                    key={role}
                    type="button"
                    onClick={() => handleQuickLogin(role)}
                    disabled={isLoading}
                    className={`text-left p-3 rounded-xl border transition-all ${bg} ${border} flex flex-col justify-between group shadow-sm disabled:opacity-50`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <PersonaIcon className="w-4 h-4 flex-shrink-0" />
                        <span className="font-bold text-xs">{cred.title}</span>
                      </div>
                      <FiArrowRight className="w-3 h-3 opacity-0 group-hover:opacity-100 group-hover:translate-x-0.5 transition-all" />
                    </div>
                    <p className="text-[11px] opacity-75 mt-1 leading-snug line-clamp-2">
                      {cred.desc}
                    </p>
                    <span className="text-[10px] font-mono mt-2 opacity-60">
                      user: {cred.username}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>
        </Card>

        {/* Security & Regulatory Note */}
        <div className="text-center text-xs text-gray-400 space-y-1">
          <p className="flex items-center justify-center gap-1.5">
            <FiLock className="w-3 h-3 text-emerald-600" />
            HIPAA 45 CFR § 164.312 Technical Safeguards Compliant
          </p>
          <p>Tokens cryptographically verified with instantaneous Redis revocation.</p>
        </div>

      </div>
    </div>
  );
}

