'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card, Button } from '@edupilot/ui';
import { lmsApi } from '@/lib/lms-api';

export default function LoginPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleEnter = async () => {
    setLoading(true);
    setError('');
    try {
      // Verify LMS scraper is reachable and session is valid
      const profile = await lmsApi.getProfile();
      if (profile?.name) {
        router.push('/dashboard');
      } else {
        setError('Could not connect to LMS. Make sure the scraper service is running.');
      }
    } catch (e: any) {
      setError(
        'Cannot connect to LMS service. Please run: python start_lms_scraper.py'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-900 px-4">
      <Card className="w-full max-w-md p-8">
        <div className="text-center mb-8">
          <div className="text-5xl mb-4">🎓</div>
          <h1 className="text-3xl font-bold text-gray-900">EduPilot</h1>
          <p className="text-gray-500 mt-2 text-sm">Iqra University AI Study Assistant</p>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded text-sm mb-6" role="alert">
            {error}
          </div>
        )}

        <div className="space-y-4">
          <Button
            variant="primary"
            className="w-full"
            onClick={handleEnter}
            disabled={loading}
            aria-label="Enter EduPilot"
          >
            {loading ? 'Connecting to LMS...' : 'Enter EduPilot'}
          </Button>

          <div className="text-center text-xs text-gray-400 space-y-1">
            <p>Authenticated as: <span className="font-medium text-gray-600">muhammad.141510.isb@iqra.edu.pk</span></p>
            <p>LMS service must be running on port 8002</p>
          </div>
        </div>
      </Card>
    </div>
  );
}
