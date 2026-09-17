'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { clsx } from 'clsx';

const navLinks = [
  { href: '/',               label: 'Home' },
  { href: '/patients',       label: 'Patients' },
  { href: '/admin/analytics', label: 'Analytics' },
  { href: '/admin/audit',     label: 'Audit Logs' },
  { href: '/about',          label: 'About' },
];

export function Navbar() {
  const pathname = usePathname();

  return (
    <header className="bg-emerald-700 text-white shadow-lg">
      <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
        {/* Brand */}
        <Link href="/" className="flex items-center gap-2 group">
          <div className="flex items-center justify-center w-9 h-9 bg-white rounded-lg shadow">
            {/* Medical Cross SVG */}
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="w-5 h-5 text-emerald-700"
            >
              <path d="M11 2h2v8h8v2h-8v8h-2v-8H3v-2h8z" stroke="none" fill="currentColor" />
            </svg>
          </div>
          <div>
            <span className="font-bold text-lg leading-tight tracking-tight group-hover:text-emerald-100 transition-colors">
              Siru HealthHub
            </span>
            <span className="block text-emerald-200 text-xs leading-tight">FHIR R4 Platform</span>
          </div>
        </Link>

        {/* Nav links */}
        <nav className="flex items-center gap-1">
          {navLinks.map(({ href, label }) => {
            const isActive =
              href === '/' ? pathname === '/' : pathname.startsWith(href);
            return (
              <Link
                key={href}
                href={href}
                className={clsx(
                  'px-4 py-2 rounded-md text-sm font-medium transition-colors duration-150',
                  isActive
                    ? 'bg-emerald-800 text-white'
                    : 'text-emerald-100 hover:bg-emerald-600 hover:text-white'
                )}
              >
                {label}
              </Link>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
