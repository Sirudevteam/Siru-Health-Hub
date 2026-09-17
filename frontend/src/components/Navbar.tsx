'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { clsx } from 'clsx';
import { FaHeartPulse } from 'react-icons/fa6';
import { FiHome, FiUsers, FiBarChart2, FiShield, FiInfo } from 'react-icons/fi';

const navLinks = [
  { href: '/',               label: 'Home',        icon: FiHome },
  { href: '/patients',       label: 'Patients',    icon: FiUsers },
  { href: '/admin/analytics', label: 'Analytics',  icon: FiBarChart2 },
  { href: '/admin/audit',     label: 'Audit Logs',  icon: FiShield },
  { href: '/about',          label: 'About',       icon: FiInfo },
];

export function Navbar() {
  const pathname = usePathname();

  return (
    <header className="bg-emerald-700 text-white shadow-lg sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-6 py-3.5 flex items-center justify-between">
        {/* Brand */}
        <Link href="/" className="flex items-center gap-2.5 group">
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
        <nav className="flex items-center gap-1">
          {navLinks.map(({ href, label, icon: Icon }) => {
            const isActive =
              href === '/' ? pathname === '/' : pathname.startsWith(href);
            return (
              <Link
                key={href}
                href={href}
                className={clsx(
                  'flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-sm font-medium transition-colors duration-150',
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
      </div>
    </header>
  );
}
