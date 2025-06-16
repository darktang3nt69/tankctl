// components/auth/login-form.tsx
'use client';

import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { loginSchema } from '@/schemas/loginSchema';
import useAuthStore from '@/store/authStore';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';
import { ThemeToggle } from '@/components/theme-toggle';
import { useEffect } from 'react';
import { login } from '@/lib/auth/authService';

export function LoginForm() {
  const router = useRouter();
  const { setApiUrl: setStoreApiUrl, login: storeLogin } = useAuthStore();

  const form = useForm<z.infer<typeof loginSchema>>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      apiKey: '',
    },
  });

  // Show validation errors as toasts
  useEffect(() => {
    const subscription = form.watch(() => {
      const errors = form.formState.errors;
      if (Object.keys(errors).length > 0) {
        const firstError = Object.values(errors)[0];
        if (firstError?.message) {
          toast.error(firstError.message, {
            duration: 3000,
          });
        }
      }
    });
    return () => subscription.unsubscribe();
  }, [form.formState.errors]);

  async function onSubmit(values: z.infer<typeof loginSchema>) {
    const { apiKey } = values;
    const apiUrl = process.env.NEXT_PUBLIC_API_URL;

    if (!apiUrl) {
      toast.error("API URL is not configured. Please set NEXT_PUBLIC_API_URL environment variable.", {
        duration: 5000,
      });
      return;
    }

    console.log('onSubmit - apiUrl:', apiUrl, 'apiKey:', apiKey);

    // Show a loading toast before the API call
    const loadingToastId = toast.loading("Authenticating...", {
      duration: Infinity,
    });

    const result = await login(apiUrl, apiKey);

    // Dismiss the loading toast
    toast.dismiss(loadingToastId);

    if (result.success) {
      storeLogin(result.token!, apiUrl);
      console.log('Auth store state after login:', useAuthStore.getState());
      toast.success("Login successful!", {
        duration: 3000,
      });
      const successMessage = encodeURIComponent("Login successful!");
      router.push(`/home?status=success&message=${successMessage}`);
    } else {
      toast.error(result.message || "Login failed", {
        duration: 5000,
      });
      const errorMessage = encodeURIComponent(result.message || "Login failed");
      router.push(`/home?status=error&message=${errorMessage}`);
    }
  }

  return (
    <Card className="w-full max-w-md mx-auto p-4 sm:p-8">
      <CardHeader className="text-center relative">
        <CardTitle>TankCtl</CardTitle>
        <CardDescription>Login to your TankCtl account</CardDescription>
        <div className="absolute top-4 right-4">
          <ThemeToggle />
        </div>
      </CardHeader>
      <CardContent>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
          <div className="grid w-full items-center gap-4">
            <div className="flex flex-col space-y-1.5">
              <Label htmlFor="apiKey">ADMIN_API_KEY</Label>
              <Input
                id="apiKey"
                type="password"
                placeholder="Your ADMIN_API_KEY"
                {...form.register('apiKey')}
              />
            </div>
          </div>
          <Button type="submit" className="w-full">
            Authenticate
          </Button>
        </form>
      </CardContent>
      <CardFooter className="flex-col text-center text-sm text-muted-foreground">
        <p>TankCtl v0.1.0</p>
        <p>
          <a href="#" className="underline underline-offset-4 hover:text-primary">
            Documentation
          </a>
          {' '}
          •
          {' '}
          <a href="#" className="underline underline-offset-4 hover:text-primary">
            Support
          </a>
        </p>
      </CardFooter>
    </Card>
  );
}