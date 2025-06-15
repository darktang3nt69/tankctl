// components/auth/login-form.tsx
'use client';

import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardHeader, CardContent, CardFooter, CardTitle, CardDescription } from '@/components/ui/card';
import { Checkbox } from "@/components/ui/checkbox";
import { loginSchema } from '@/schemas/loginSchema';
import { login } from '@/lib/auth/authService';
import { useEffect, useState } from 'react';
import useAuthStore from '@/store/authStore';
import { useRouter } from 'next/navigation';

export function LoginForm() {
  const router = useRouter();
  const { setApiUrl: setStoreApiUrl, login: storeLogin } = useAuthStore();

  const [isRemembered, setIsRemembered] = useState(false);

  const form = useForm<z.infer<typeof loginSchema>>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      apiUrl: '',
      apiKey: '',
    },
  });

  useEffect(() => {
    const rememberedUrl = localStorage.getItem("rememberedApiUrl");
    if (rememberedUrl) {
      form.setValue("apiUrl", rememberedUrl);
      setIsRemembered(true); // Set checkbox state if URL is remembered
    }
  }, [form]);

  async function onSubmit(values: z.infer<typeof loginSchema>) {
    const { apiUrl, apiKey } = values;
    console.log('onSubmit - apiUrl:', apiUrl, 'apiKey:', apiKey);

    // Update localStorage based on current checkbox state
    if (isRemembered && apiUrl) {
      localStorage.setItem("rememberedApiUrl", apiUrl);
    } else if (!isRemembered) {
      localStorage.removeItem("rememberedApiUrl");
    }

    const result = await login(apiUrl, apiKey);

    if (result.success) {
      storeLogin(result.token!, apiUrl);
      // Log the state immediately after updating the store
      console.log('Auth store state after login:', useAuthStore.getState());
      router.push('/home'); // Redirect to home or dashboard after successful login
    } else {
      // Display error message to the user
      alert(result.message || "Login failed");
  
    }
  }

  return (
    <Card className="w-full max-w-md mx-auto p-4 sm:p-8">
      <CardHeader className="text-center">
        <CardTitle>TankCtl</CardTitle>
        <CardDescription>Login to your TankCtl account</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
          <div className="grid w-full items-center gap-4">
            <div className="flex flex-col space-y-1.5">
              <Label htmlFor="apiUrl">API Server URL</Label>
              <Input
                id="apiUrl"
                placeholder="e.g., http://localhost:8080"
                {...form.register('apiUrl')}
              />
              {form.formState.errors.apiUrl && (
                <p className="text-red-500 text-sm">
                  {form.formState.errors.apiUrl.message}
                </p>
              )}
            </div>
            <div className="flex flex-col space-y-1.5">
              <Label htmlFor="apiKey">ADMIN_API_KEY</Label>
              <Input
                id="apiKey"
                type="password"
                placeholder="Your ADMIN_API_KEY"
                {...form.register('apiKey')}
              />
              {form.formState.errors.apiKey && (
                <p className="text-red-500 text-sm">
                  {form.formState.errors.apiKey.message}
                </p>
              )}
            </div>
            <div className="flex items-center space-x-2">
              <Checkbox
                id="rememberUrl"
                checked={isRemembered}
                onCheckedChange={(checked) => {
                  setIsRemembered(checked === true);
                  // The localStorage update will happen in onSubmit if the form is submitted
                  // or explicitly here if needed immediately, but better to tie to form state
                  if (!checked) {
                    localStorage.removeItem("rememberedApiUrl");
                  }
                }}
              />
              <Label htmlFor="rememberUrl">Remember API URL</Label>
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