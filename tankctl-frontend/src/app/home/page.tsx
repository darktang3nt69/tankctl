import { FlashToastDisplay } from '@/components/flash-toast-display';

export default function HomePage() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <h1>Welcome to TankCtl!</h1>
      <p>This is your home page.</p>
      <FlashToastDisplay />
    </div>
  );
} 