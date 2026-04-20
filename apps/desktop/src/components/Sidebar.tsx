'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useOffline } from '@/lib/offline';

const NAV = [
  { href: '/dashboard', label: 'Dashboard', short: 'DB' },
  { href: '/courses', label: 'Courses', short: 'CR' },
  { href: '/assignments', label: 'Assignments', short: 'AS' },
  { href: '/grades', label: 'Grades', short: 'GR' },
  { href: '/events', label: 'Calendar', short: 'EV' },
  { href: '/lectures', label: 'Lectures', short: 'LC' },
  { href: '/query', label: 'Ask AI', short: 'AI' },
  { href: '/settings', label: 'Settings', short: 'ST' },
];

export function Sidebar() {
  const pathname = usePathname();
  const { isOnline } = useOffline();

  return (
    <aside className="sticky top-0 hidden h-screen w-[300px] shrink-0 p-5 lg:block">
      <div className="panel flex h-full flex-col rounded-[36px] border border-white/70 bg-white/80 px-5 py-6">
        <div className="flex items-center gap-3 border-b border-slate-200/80 pb-5">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-950 text-sm font-semibold tracking-[0.24em] text-white">
            EP
          </div>
          <div>
            <h1 className="text-lg font-semibold tracking-tight text-slate-950">EduPilot</h1>
            <p className="mt-1 text-xs uppercase tracking-[0.24em] text-slate-400">Student workspace</p>
          </div>
        </div>

        <div className="mt-5 rounded-[24px] border border-slate-200/80 bg-slate-50/90 p-4">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-semibold uppercase tracking-[0.2em] text-slate-400">Status</span>
            <span
              className={`rounded-full px-2.5 py-1 text-[11px] font-medium ${
                isOnline ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'
              }`}
            >
              {isOnline ? 'Online' : 'Offline'}
            </span>
          </div>
          <p className="mt-3 text-sm leading-6 text-slate-600">
            Clean focus mode for courses, assignments, grades, and daily university work.
          </p>
        </div>

        <nav className="mt-6 flex-1 space-y-1.5" aria-label="Main navigation">
          {NAV.map(({ href, label, short }) => {
            const active = pathname === href || pathname.startsWith(`${href}?`);
            return (
              <Link
                key={href}
                href={href}
                className={`group flex items-center gap-3 rounded-2xl px-3 py-3 transition-all duration-200 ${
                  active
                    ? 'bg-slate-950 text-white shadow-lg shadow-slate-900/10'
                    : 'text-slate-500 hover:bg-white hover:text-slate-950'
                }`}
                aria-current={active ? 'page' : undefined}
              >
                <span
                  className={`flex h-10 w-10 items-center justify-center rounded-2xl text-[11px] font-semibold tracking-[0.16em] ${
                    active ? 'bg-white/14 text-white' : 'bg-slate-100 text-slate-500 group-hover:bg-slate-950 group-hover:text-white'
                  }`}
                >
                  {short}
                </span>
                <div className="min-w-0">
                  <p className={`text-sm font-medium ${active ? 'text-white' : 'text-slate-700'}`}>{label}</p>
                  <p className={`text-xs ${active ? 'text-slate-300' : 'text-slate-400'}`}>
                    {label === 'Ask AI' ? 'Study with context' : 'Open workspace'}
                  </p>
                </div>
              </Link>
            );
          })}
        </nav>

        <div className="mt-6 rounded-[24px] border border-slate-200/80 bg-white/90 p-4">
          <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-400">Workspace</p>
          <p className="mt-2 text-sm font-medium text-slate-800">Muhammad Danish</p>
          <p className="mt-1 text-sm leading-6 text-slate-500">Minimal academic desktop with direct LMS sync.</p>
        </div>
      </div>
    </aside>
  );
}
