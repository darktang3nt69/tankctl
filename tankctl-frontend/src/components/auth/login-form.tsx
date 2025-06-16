// components/auth/login-form.tsx
'use client';

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardHeader, CardContent, CardFooter, CardTitle, CardDescription } from '@/components/ui/card';
import { loginSchema } from '@/schemas/loginSchema';
import { login } from '@/lib/auth/authService';
import useAuthStore from '@/store/authStore';
import { useRouter } from 'next/navigation';
import { ThemeToggle } from '@/components/theme-toggle';
import { toast } from 'sonner';
import { useEffect } from 'react';

export function LoginForm() {
  const router = useRouter();
  const { setApiUrl: setStoreApiUrl, login: storeLogin } = useAuthStore();

  const form = useForm<z.infer<typeof loginSchema>>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      apiKey: '',
    },
  });

  useEffect(() => {
    const errors = form.formState.errors;
    if (Object.keys(errors).length > 0) {
      const firstErrorKey = Object.keys(errors)[0];
      const errorMessage = (errors as any)[firstErrorKey]?.message;
      if (errorMessage) {
        toast.error(`Validation Error: ${errorMessage}`);
      }
    }
  }, [form.formState.errors]);

  async function onSubmit(values: z.infer<typeof loginSchema>) {
    const { apiKey } = values;
    const apiUrl = process.env.NEXT_PUBLIC_API_URL;

    if (!apiUrl) {
      toast.error("API URL is not configured. Please set NEXT_PUBLIC_API_URL environment variable.");
      return;
    }

    console.log('onSubmit - apiUrl:', apiUrl, 'apiKey:', apiKey);

    // Show a loading toast before the API call
    const loadingToastId = toast.loading("Authenticating...");

    const result = await login(apiUrl, apiKey);

    // Dismiss the loading toast
    toast.dismiss(loadingToastId);

    if (result.success) {
      storeLogin(result.token!, apiUrl);
      console.log('Auth store state after login:', useAuthStore.getState());
      const successMessage = encodeURIComponent("Login successful!");
      router.push(`/home?status=success&message=${successMessage}`);
    } else {
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