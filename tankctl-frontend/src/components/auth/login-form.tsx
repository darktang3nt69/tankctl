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
import { Loader2 } from 'lucide-react';
import packageJson from '../../../package.json';

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
    <div className="min-h-screen flex items-center justify-center p-4 arcane-gradient">
      <Card className="w-full max-w-md arcane-card">
        <CardHeader className="space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-3xl font-bold tracking-tight arcane-text-gradient">TankCtl</CardTitle>
              <CardDescription className="text-muted-foreground/80 mt-1">
                Login to your TankCtl account
              </CardDescription>
            </div>
            <ThemeToggle />
          </div>
        </CardHeader>
        <form onSubmit={form.handleSubmit(onSubmit)}>
          <CardContent className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="apiKey" className="text-sm font-medium text-muted-foreground/90">
                API Key
              </Label>
              <Input
                id="apiKey"
                type="password"
                placeholder="Enter your API key"
                className="arcane-input h-11"
                {...form.register('apiKey')}
                disabled={form.formState.isSubmitting}
              />
            </div>
          </CardContent>
          <CardFooter className="flex flex-col space-y-4">
            <Button 
              type="submit" 
              className="w-full arcane-button h-11"
              disabled={form.formState.isSubmitting}
            >
              {form.formState.isSubmitting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Authenticating...
                </>
              ) : (
                'Authenticate'
              )}
            </Button>
            <div className="text-center text-sm text-muted-foreground/70 space-y-2">
              <p className="font-medium">Version {packageJson.version}</p>
              <div className="flex items-center justify-center space-x-3">
                <a 
                  href="https://docs.tankctl.com" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-primary/90 hover:text-primary transition-colors arcane-border px-3 py-1 rounded-md"
                >
                  Documentation
                </a>
                <a 
                  href="https://support.tankctl.com" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-primary/90 hover:text-primary transition-colors arcane-border px-3 py-1 rounded-md"
                >
                  Support
                </a>
              </div>
            </div>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}