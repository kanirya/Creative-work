'use client';

import { usePathname } from 'next/navigation';
import { Sidebar } from './Sidebar';

// Pages that don't use the sidebar (login)
const NO_SIDEBAR = ['/login', '/'];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const showSidebar = !NO_SIDEBAR.includes(pathname);

  if (!showSidebar) {
    return <>{children}</>;
  }

  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar />
      <main className="flex-1 overflow-auto" role="main">
        {children}
      </main>
    </div>
  );
}
