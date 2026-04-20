'use client';

import { usePathname } from 'next/navigation';
import { Sidebar } from './Sidebar';

// Pages that don't use the sidebar (login)
const NO_SIDEBAR = ['/login', '/'];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const showSidebar = !NO_SIDEBAR.includes(pathname);

  if (!showSidebar) {
    return (
      <div className="min-h-screen bg-transparent">
        {children}
      </div>
    );
  }

  return (
    <div className="relative min-h-screen overflow-hidden bg-transparent">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute left-[-8rem] top-[-8rem] h-72 w-72 rounded-full bg-white/60 blur-3xl" />
        <div className="absolute right-[-10rem] top-20 h-80 w-80 rounded-full bg-slate-200/35 blur-3xl" />
      </div>

      <div className="relative flex min-h-screen">
        <Sidebar />
        <main className="flex-1 overflow-auto" role="main">
          <div className="mx-auto min-h-screen w-full max-w-[1600px]">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
