'use client';

import { Loader2 } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';

interface LoadingScreenProps {
  message?: string;
}

export function LoadingScreen({ message = 'Loading...' }: LoadingScreenProps) {
  return (
    <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center">
      <Card className="w-[350px]">
        <CardContent className="pt-6">
          <div className="flex flex-col items-center gap-4">
            <div className="flex items-center gap-2">
              <Loader2 className="h-4 w-4 animate-spin text-primary" />
              <span className="text-sm text-muted-foreground">{message}</span>
            </div>
            <div className="space-y-2 w-full">
              <div className="h-4 w-full rounded-md bg-muted animate-pulse" />
              <div className="h-4 w-[80%] rounded-md bg-muted animate-pulse" />
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
} 