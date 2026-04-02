'use client';

import { useOffline } from '@/lib/offline';

export function OfflineIndicator() {
  const { isOnline } = useOffline();

  if (isOnline) return null;

  return (
    <div 
      className="fixed top-0 left-0 right-0 bg-yellow-500 text-white text-center py-2 text-sm z-50"
      role="alert"
      aria-live="polite"
    >
      You are currently offline. Queries will be queued and processed when you reconnect.
    </div>
  );
}
