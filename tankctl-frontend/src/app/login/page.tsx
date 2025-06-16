'use client';

import { LoginForm } from '@/components/auth/login-form';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';
import useAuthStore from '@/store/authStore';

export default function LoginPage() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();

  useEffect(() => {
    if (isAuthenticated) {
      router.replace('/home');
    }
  }, [isAuthenticated, router]);

  // Optionally, return null or a loading spinner while checking auth status
  if (isAuthenticated) {
    return null; // Or a loading spinner
  }

  return (
    <div className="flex min-h-screen items-center justify-center">
      <LoginForm />
    </div>
  );
} 