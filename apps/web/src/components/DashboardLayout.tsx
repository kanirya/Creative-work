'use client';

import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { tokenStorage } from '@/lib/auth';
import { Button } from '@edupilot/ui';

export function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();

  const handleLogout = () => {
    tokenStorage.clearTokens();
    router.push('/login');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="bg-white shadow-sm border-b border-gray-200" role="navigation" aria-label="Main navigation">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-8">
              <Link href="/dashboard" className="text-xl font-bold text-gray-900" aria-label="EduPilot home">
                EduPilot
              </Link>
              <div className="hidden md:flex space-x-4" role="menubar">
                <Link
                  href="/dashboard"
                  className="text-gray-700 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium focus:outline-none focus:ring-2 focus:ring-blue-500"
                  role="menuitem"
                >
                  Dashboard
                </Link>
                <Link
                  href="/query"
                  className="text-gray-700 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium focus:outline-none focus:ring-2 focus:ring-blue-500"
                  role="menuitem"
                >
                  Ask AI
                </Link>
                <Link
                  href="/lectures"
                  className="text-gray-700 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium focus:outline-none focus:ring-2 focus:ring-blue-500"
                  role="menuitem"
                >
                  Lectures
                </Link>
              </div>
            </div>
            <Button variant="secondary" size="sm" onClick={handleLogout} aria-label="Logout from your account">
              Logout
            </Button>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8" role="main">
        {children}
      </main>
    </div>
  );
}
