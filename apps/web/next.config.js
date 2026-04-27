/** @type {import('next').NextConfig} */
const apiGatewayUrl = (
  process.env.API_GATEWAY_URL ||
  'http://localhost:5000'
).replace(/\/$/, '');

const nextConfig = {
  reactStrictMode: true,
  transpilePackages: ['@edupilot/ui', '@edupilot/types', '@edupilot/api-client', '@edupilot/utils'],
  output: 'standalone',
  eslint: {
    // Disable ESLint during builds for now
    ignoreDuringBuilds: true,
  },
  typescript: {
    // Disable type checking during builds for now
    ignoreBuildErrors: true,
  },
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || '/proxy',
  },
  images: {
    formats: ['image/avif', 'image/webp'],
  },
  experimental: {
    optimizePackageImports: ['@edupilot/ui', '@edupilot/types'],
  },
  async rewrites() {
    return [
      {
        source: '/proxy/api/:path*',
        destination: `${apiGatewayUrl}/api/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
