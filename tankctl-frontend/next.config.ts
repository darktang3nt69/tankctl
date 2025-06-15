import type { NextConfig } from "next";
import withPWA from "next-pwa";

const ContentSecurityPolicy = `
  default-src 'self';
  script-src 'self' 'unsafe-eval' 'unsafe-inline';
  style-src 'self' 'unsafe-inline';
  connect-src 'self' https://api.darktang3nt.cloud http://localhost:8000;
  img-src 'self' data:;
  font-src 'self';
  object-src 'none';
  media-src 'none';
  frame-src 'none';
`;

const nextConfig = {
  reactStrictMode: true,
  headers: async () => {
    return [
      {
        source: "/:path*",
        headers: [
          {
            key: "Content-Security-Policy",
            value: ContentSecurityPolicy.replace(/\n/g, ''),
          },
        ],
      },
    ];
  },
  /* config options here */
};

// @ts-ignore
export default withPWA({
  dest: "public",
  register: true,
  skipWaiting: true,
})(nextConfig);
