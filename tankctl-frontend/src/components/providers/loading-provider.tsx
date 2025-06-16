'use client';

import { LoadingScreen } from '@/components/ui/loading-screen';
import useAuthStore from '@/store/authStore';

export function LoadingProvider({ children }: { children: React.ReactNode }) {
  const isLoading = useAuthStore((state) => state.isLoading);

  return (
    <>
      {isLoading && <LoadingScreen message="Loading application..." />}
      {children}
    </>
  );
} 