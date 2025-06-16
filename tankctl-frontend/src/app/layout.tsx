import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "@/components/providers";
import { Toaster } from 'sonner';

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "TankCtl",
  description: "Dashboard to manage your aquatic worlds",
  manifest: "/manifest.json",
  icons: {
    icon: [
      { url: '/icons/icon-48x48.png', sizes: '48x48' },
      { url: '/icons/icon-72x72.png', sizes: '72x72' },
      { url: '/icons/icon-96x96.png', sizes: '96x96' },
      { url: '/icons/icon-128x128.png', sizes: '128x128' },
      { url: '/icons/icon-144x144.png', sizes: '144x144' },
      { url: '/icons/icon-152x152.png', sizes: '152x152' },
      { url: '/icons/icon-192x192.png', sizes: '192x192' },
      { url: '/icons/icon-256x256.png', sizes: '256x256' },
      { url: '/icons/icon-384x384.png', sizes: '384x384' },
      { url: '/icons/icon-512x512.png', sizes: '512x512' }
    ],
    apple: [
      { url: '/icons/icon-152x152.png', sizes: '152x152' }
    ]
  }
};

export const viewport = {
  themeColor: "#000000",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link rel="manifest" href="/manifest.json" />
        <link rel="icon" href="/icons/icon-48x48.png" sizes="48x48" />
        <link rel="icon" href="/icons/icon-72x72.png" sizes="72x72" />
        <link rel="icon" href="/icons/icon-96x96.png" sizes="96x96" />
        <link rel="icon" href="/icons/icon-128x128.png" sizes="128x128" />
        <link rel="icon" href="/icons/icon-144x144.png" sizes="144x144" />
        <link rel="icon" href="/icons/icon-152x152.png" sizes="152x152" />
        <link rel="icon" href="/icons/icon-192x192.png" sizes="192x192" />
        <link rel="icon" href="/icons/icon-256x256.png" sizes="256x256" />
        <link rel="icon" href="/icons/icon-384x384.png" sizes="384x384" />
        <link rel="icon" href="/icons/icon-512x512.png" sizes="512x512" />
        <link rel="apple-touch-icon" href="/icons/icon-152x152.png" />
      </head>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
          {children}
        </ThemeProvider>
        <Toaster richColors position="bottom-right" />
      </body>
    </html>
  );
}
