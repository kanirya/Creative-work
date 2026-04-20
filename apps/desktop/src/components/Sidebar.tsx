'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { motion } from 'framer-motion';
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
    <aside className="sticky top-0 hidden h-screen min-h-0 w-[272px] shrink-0 p-4 lg:block">
      <div className="panel flex h-[calc(100vh-2rem)] min-h-0 flex-col rounded-[32px] border border-white/70 bg-white/80 px-4 py-5">
        <div className="flex items-center gap-3 border-b border-slate-200/80 pb-4">
          <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-slate-950 text-xs font-semibold tracking-[0.24em] text-white">
            EP
          </div>
          <div>
            <h1 className="text-base font-semibold tracking-tight text-slate-950">EduPilot</h1>
            <p className="mt-1 text-[11px] uppercase tracking-[0.24em] text-slate-400">Student workspace</p>
          </div>
        </div>

        <div className="mt-4 rounded-[22px] border border-slate-200/80 bg-slate-50/90 p-3.5">
          <div className="flex items-center justify-between">
            <span className="text-[10px] font-semibold uppercase tracking-[0.2em] text-slate-400">Status</span>
            <span
              className={`rounded-full px-2.5 py-1 text-[10px] font-medium ${
                isOnline ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'
              }`}
            >
              {isOnline ? 'Online' : 'Offline'}
            </span>
          </div>
          <p className="mt-2.5 text-xs leading-6 text-slate-600">
            Clean focus mode for courses, assignments, grades, and daily university work.
          </p>
        </div>

        <nav className="mt-5 min-h-0 flex-1 space-y-1.5 overflow-y-auto pr-1" aria-label="Main navigation">
          {NAV.map(({ href, label, short }, index) => {
            const active = pathname === href || pathname.startsWith(`${href}?`);
            return (
              <motion.div
                key={href}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.03, duration: 0.22 }}
              >
                <Link
                  href={href}
                  className={`group flex items-center gap-3 rounded-2xl px-3 py-2.5 transition-all duration-200 ${
                    active
                      ? 'bg-slate-950 text-white shadow-lg shadow-slate-900/10'
                      : 'text-slate-500 hover:bg-white hover:text-slate-950'
                  }`}
                  aria-current={active ? 'page' : undefined}
                >
                  <span
                    className={`flex h-9 w-9 items-center justify-center rounded-2xl text-[10px] font-semibold tracking-[0.16em] ${
                      active ? 'bg-white/14 text-white' : 'bg-slate-100 text-slate-500 group-hover:bg-slate-950 group-hover:text-white'
                    }`}
                  >
                    {short}
                  </span>
                  <div className="min-w-0">
                    <p className={`text-sm font-medium ${active ? 'text-white' : 'text-slate-700'}`}>{label}</p>
                    <p className={`text-[11px] ${active ? 'text-slate-300' : 'text-slate-400'}`}>
                      {label === 'Ask AI' ? 'Study with context' : 'Open workspace'}
                    </p>
                  </div>
                </Link>
              </motion.div>
            );
          })}
        </nav>

        <div className="mt-4 rounded-[22px] border border-slate-200/80 bg-white/90 p-3.5">
          <p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-slate-400">Workspace</p>
          <p className="mt-2 text-sm font-medium text-slate-800">Muhammad Danish</p>
          <p className="mt-1 text-xs leading-6 text-slate-500">Minimal academic desktop with direct LMS sync.</p>
        </div>
      </div>
    </aside>
  );
}
