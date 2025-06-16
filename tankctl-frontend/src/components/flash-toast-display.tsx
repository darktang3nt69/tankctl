'use client';

import { useEffect } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { toast } from 'sonner';

export function FlashToastDisplay() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const status = searchParams.get('status');
  const message = searchParams.get('message');

  useEffect(() => {
    if (status && message) {
      const decodedMessage = decodeURIComponent(message);
      if (status === 'success') {
        toast.success(decodedMessage);
      } else if (status === 'error') {
        toast.error(decodedMessage);
      } else if (status === 'info') {
        toast.info(decodedMessage);
      } else if (status === 'warning') {
        toast.warning(decodedMessage);
      }

      // Clean up the URL by removing the query parameters
      // This ensures the toast doesn't reappear on refresh
      const newSearchParams = new URLSearchParams(searchParams.toString());
      newSearchParams.delete('status');
      newSearchParams.delete('message');
      router.replace(`?${newSearchParams.toString()}`, { scroll: false });
    }
  }, [status, message, router, searchParams]);

  return null; // This component doesn't render anything visible directly
} 