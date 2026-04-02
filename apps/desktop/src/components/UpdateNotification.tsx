'use client';

import { useEffect, useState } from 'react';
import { Button, Card } from '@edupilot/ui';

export function UpdateNotification() {
  const [updateAvailable, setUpdateAvailable] = useState(false);
  const [updateDownloaded, setUpdateDownloaded] = useState(false);

  useEffect(() => {
    if (typeof window !== 'undefined' && window.electron) {
      window.electron.onUpdateAvailable(() => {
        setUpdateAvailable(true);
      });

      window.electron.onUpdateDownloaded(() => {
        setUpdateDownloaded(true);
      });
    }
  }, []);

  if (!updateAvailable) return null;

  return (
    <div className="fixed bottom-4 right-4 z-50">
      <Card className="p-4 shadow-lg max-w-sm">
        <h3 className="font-semibold text-gray-900 mb-2">
          {updateDownloaded ? 'Update Ready' : 'Update Available'}
        </h3>
        <p className="text-sm text-gray-600 mb-4">
          {updateDownloaded
            ? 'A new version has been downloaded and is ready to install.'
            : 'A new version of EduPilot is available and downloading.'}
        </p>
        {updateDownloaded && (
          <Button
            variant="primary"
            size="sm"
            onClick={() => window.electron?.installUpdate()}
            className="w-full"
          >
            Install and Restart
          </Button>
        )}
      </Card>
    </div>
  );
}
