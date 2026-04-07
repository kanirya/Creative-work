'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useOffline } from '@/lib/offline';

const NAV = [
  { href: '/dashboard',   label: 'Dashboard',    icon: '🏠' },
  { href: '/courses',     label: 'Courses',       icon: '📚' },
  { href: '/assignments', label: 'Assignments',   icon: '📝' },
  { href: '/grades',      label: 'Grades',        icon: '📊' },
  { href: '/events',      label: 'Calendar',      icon: '📅' },
  { href: '/lectures',    label: 'Lectures',      icon: '🎥' },
  { href: '/query',       label: 'Ask AI',        icon: '🤖' },
  { href: '/settings',    label: 'Settings',      icon: '⚙️' },
];

export function Sidebar() {
  const pathname = usePathname();
  const { isOnline } = useOffline();

  return (
    <aside className="w-56 min-h-screen bg-gray-900 text-white flex flex-col">
      {/* Logo */}
      <div className="px-5 py-5 border-b border-gray-700">
        <h1 className="text-xl font-bold text-white">EduPilot</h1>
        <p className="text-xs text-gray-400 mt-0.5">Iqra University LMS</p>
      </div>

      {/* Offline badge */}
      {!isOnline && (
        <div className="mx-3 mt-3 px-3 py-1.5 bg-yellow-900 text-yellow-300 text-xs rounded">
          ⚠ Offline mode
        </div>
      )}

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-1" aria-label="Main navigation">
        {NAV.map(({ href, label, icon }) => {
          const active = pathname === href || pathname.startsWith(href + '?');
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                active
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-300 hover:bg-gray-800 hover:text-white'
              }`}
              aria-current={active ? 'page' : undefined}
            >
              <span>{icon}</span>
              {label}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="px-5 py-4 border-t border-gray-700 text-xs text-gray-500">
        MUHAMMAD DANISH
      </div>
    </aside>
  );
}
