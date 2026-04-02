'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { tokenStorage } from '@/lib/auth';

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const router = useRouter();

  useEffect(() => {
    const tokens = tokenStorage.getTokens();
    if (!tokens) {
      router.push('/login');
    }
  }, [router]);

  const tokens = tokenStorage.getTokens();
  if (!tokens) {
    return null;
  }

  return <>{children}</>;
}
