'use client';

import { FlashToastDisplay } from '@/components/flash-toast-display';
import { withAuth } from '@/components/auth/with-auth';

function HomePage() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <h1>Welcome to TankCtl!</h1>
      <p>This is your home page.</p>
      <FlashToastDisplay />
    </div>
  );
}

export default withAuth(HomePage); 