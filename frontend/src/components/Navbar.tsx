'use client';

import React, { useState, useRef, useEffect } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { clsx } from 'clsx';
import { FaHeartPulse, FaUserDoctor, FaUserNurse, FaShieldHalved, FaHospitalUser } from 'react-icons/fa6';
import {
  FiHome,
  FiUsers,
  FiBarChart2,
  FiShield,
  FiInfo,
  FiLogIn,
  FiLogOut,
  FiChevronDown,
  FiUser,
  FiRepeat
} from 'react-icons/fi';
import { useAuth, DEMO_CREDENTIALS, UserRole } from '@/context/AuthContext';

const navLinks = [
  { href: '/',               label: 'Home',        icon: FiHome },
  { href: '/patients',       label: 'Patients',    icon: FiUsers },
  { href: '/admin/analytics', label: 'Analytics',  icon: FiBarChart2 },
  { href: '/admin/audit',     label: 'Audit Logs',  icon: FiShield },
  { href: '/about',          label: 'About',       icon: FiInfo },
];

export function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, isAuthenticated, logout, switchDemoUser } = useAuth();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setDropdownOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleLogout = async () => {
    setDropdownOpen(false);
    await logout();
    router.push('/login');
  };

  const handleSwitchPersona = async (role: UserRole) => {
    setDropdownOpen(false);
    const loggedUser = await switchDemoUser(role);
    if (role === 'PATIENT' && loggedUser.patient_id) {
      router.push(`/patients/${loggedUser.patient_id}`);
    } else if (role === 'ADMIN') {
      router.push('/admin/analytics');
    } else {
      router.push('/patients');
    }
  };

  const getRoleBadge = (role: UserRole) => {
    switch (role) {
      case 'ADMIN':
        return { label: 'ADMIN', color: 'bg-purple-100 text-purple-900 border-purple-300', icon: FaShieldHalved };
      case 'DOCTOR':
        return { label: 'DOCTOR', color: 'bg-emerald-100 text-emerald-900 border-emerald-300', icon: FaUserDoctor };
      case 'NURSE':
        return { label: 'NURSE', color: 'bg-blue-100 text-blue-900 border-blue-300', icon: FaUserNurse };
      case 'PATIENT':
        return { label: 'PATIENT', color: 'bg-amber-100 text-amber-900 border-amber-300', icon: FaHospitalUser };
    }
  };

  return (
    <header className="bg-emerald-700 text-white shadow-lg sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-6 py-3 flex items-center justify-between gap-4">
        {/* Brand */}
        <Link href="/" className="flex items-center gap-2.5 group flex-shrink-0">
          <div className="flex items-center justify-center w-10 h-10 bg-white rounded-xl shadow-md group-hover:scale-105 transition-transform">
            <FaHeartPulse className="w-5 h-5 text-emerald-700" />
          </div>
          <div>
            <span className="font-bold text-lg leading-tight tracking-tight group-hover:text-emerald-100 transition-colors flex items-center gap-1.5">
              Siru HealthHub
            </span>
            <span className="block text-emerald-200 text-xs font-medium tracking-wide">Enterprise FHIR R4 Platform</span>
          </div>
        </Link>

        {/* Nav links */}
        <nav className="hidden md:flex items-center gap-1">
          {navLinks.map(({ href, label, icon: Icon }) => {
            const isActive =
              href === '/' ? pathname === '/' : pathname.startsWith(href);
            return (
              <Link
                key={href}
                href={href}
                className={clsx(
                  'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors duration-150',
                  isActive
                    ? 'bg-emerald-800 text-white shadow-inner'
                    : 'text-emerald-100 hover:bg-emerald-600 hover:text-white'
                )}
              >
                <Icon className="w-4 h-4 opacity-90" />
                {label}
              </Link>
            );
          })}
        </nav>

        {/* User Auth Section */}
        <div className="flex items-center gap-3" ref={dropdownRef}>
          {isAuthenticated && user ? (
            <div className="relative">
              <button
                onClick={() => setDropdownOpen(!dropdownOpen)}
                className="flex items-center gap-2 bg-emerald-800/80 hover:bg-emerald-800 text-white px-3 py-1.5 rounded-xl border border-emerald-600 transition shadow-sm text-xs font-medium"
                aria-expanded={dropdownOpen}
              >
                {(() => {
                  const badge = getRoleBadge(user.role);
                  const BadgeIcon = badge.icon;
                  return (
                    <>
                      <div className="w-6 h-6 rounded-full bg-white text-emerald-700 flex items-center justify-center font-bold text-xs">
                        <BadgeIcon className="w-3.5 h-3.5" />
                      </div>
                      <div className="text-left hidden sm:block">
                        <p className="font-semibold text-white leading-tight font-mono text-xs">{user.username}</p>
                        <p className="text-[10px] text-emerald-200 leading-tight">{badge.label}</p>
                      </div>
                      <FiChevronDown className={`w-3.5 h-3.5 text-emerald-300 transition-transform ${dropdownOpen ? 'rotate-180' : ''}`} />
                    </>
                  );
                })()}
              </button>

              {/* Dropdown Menu */}
              {dropdownOpen && (
                <div className="absolute right-0 mt-2 w-72 bg-white rounded-2xl shadow-2xl border border-gray-200 py-2 text-gray-800 z-50 text-xs animate-in fade-in duration-100">
                  <div className="px-4 py-3 border-b border-gray-100">
                    <p className="text-gray-400 text-[10px] font-semibold uppercase tracking-wider">Signed In User</p>
                    <p className="font-bold text-gray-900 text-sm mt-0.5">{user.username}</p>
                    <div className="flex items-center gap-1.5 mt-1.5">
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${getRoleBadge(user.role).color}`}>
                        ROLE: {user.role}
                      </span>
                      {user.patient_id && (
                        <span className="text-[10px] text-gray-500 font-mono bg-gray-100 px-1.5 py-0.5 rounded">
                          ID: {user.patient_id}
                        </span>
                      )}
                      {user.practitioner_id && (
                        <span className="text-[10px] text-gray-500 font-mono bg-gray-100 px-1.5 py-0.5 rounded">
                          ID: {user.practitioner_id}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Patient Quick Link */}
                  {user.role === 'PATIENT' && user.patient_id && (
                    <div className="p-2 border-b border-gray-100">
                      <Link
                        href={`/patients/${user.patient_id}`}
                        onClick={() => setDropdownOpen(false)}
                        className="flex items-center gap-2 px-3 py-2 text-emerald-700 font-semibold bg-emerald-50 rounded-xl hover:bg-emerald-100 transition"
                      >
                        <FiUser className="w-3.5 h-3.5" /> View My Health Record
                      </Link>
                    </div>
                  )}

                  {/* Switch Demo Persona */}
                  <div className="px-3 py-2 border-b border-gray-100">
                    <p className="text-gray-400 text-[10px] font-semibold uppercase tracking-wider mb-2 flex items-center gap-1">
                      <FiRepeat className="w-3 h-3 text-emerald-600" /> Switch Demo Role
                    </p>
                    <div className="grid grid-cols-2 gap-1.5">
                      {(['ADMIN', 'DOCTOR', 'NURSE', 'PATIENT'] as UserRole[]).map((r) => {
                        const isCurrent = user.role === r;
                        return (
                          <button
                            key={r}
                            onClick={() => handleSwitchPersona(r)}
                            className={clsx(
                              'text-left px-2.5 py-1.5 rounded-lg text-[11px] font-medium transition border',
                              isCurrent
                                ? 'bg-emerald-50 text-emerald-800 border-emerald-300 font-bold'
                                : 'hover:bg-gray-50 text-gray-600 border-gray-200'
                            )}
                          >
                            {r}
                          </button>
                        );
                      })}
                    </div>
                  </div>

                  {/* Sign Out */}
                  <div className="p-1.5">
                    <button
                      onClick={handleLogout}
                      className="w-full flex items-center gap-2 px-3 py-2 text-rose-600 hover:bg-rose-50 rounded-xl font-semibold transition text-left"
                    >
                      <FiLogOut className="w-4 h-4" /> Sign Out (Revoke Session)
                    </button>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <Link
              href="/login"
              className="inline-flex items-center gap-1.5 px-4 py-1.5 bg-white text-emerald-800 hover:bg-emerald-50 rounded-xl font-semibold text-xs transition shadow-sm"
            >
              <FiLogIn className="w-3.5 h-3.5" /> Sign In
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}
