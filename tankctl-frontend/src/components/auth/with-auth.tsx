'use client';

import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import useAuthStore from '@/store/authStore';

interface WithAuthProps {
  children: React.ReactNode;
}

export function withAuth<P extends object>(Component: React.ComponentType<P>) {
  const AuthenticatedComponent = (props: P) => {
    const router = useRouter();
    const { isAuthenticated } = useAuthStore();

    useEffect(() => {
      if (!isAuthenticated) {
        router.replace('/login'); // Redirect to login if not authenticated
      }
    }, [isAuthenticated, router]);

    if (!isAuthenticated) {
      // Optionally, show a loading spinner or null while redirecting
      return null; 
    }

    return <Component {...props} />;
  };

  AuthenticatedComponent.displayName = `withAuth(${Component.displayName || Component.name || 'Component'})`;

  return AuthenticatedComponent;
} 