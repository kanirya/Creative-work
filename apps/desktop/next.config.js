/** @type {import('next').NextConfig} */
const apiGatewayUrl = (
  process.env.API_GATEWAY_URL ||
  'http://localhost:5000'
).replace(/\/$/, '');

const lmsScraperUrl = (
  process.env.LMS_SCRAPER_URL ||
  'http://localhost:8002'
).replace(/\/$/, '');

const nextConfig = {
  reactStrictMode: true,
  transpilePackages: ['@edupilot/ui', '@edupilot/types', '@edupilot/api-client', '@edupilot/utils'],
  distDir: '.next',
  images: {
    unoptimized: true,
  },
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || '/proxy',
    NEXT_PUBLIC_LMS_SCRAPER_URL: process.env.NEXT_PUBLIC_LMS_SCRAPER_URL || '/proxy/lms',
  },
  async rewrites() {
    return [
      {
        source: '/proxy/api/:path*',
        destination: `${apiGatewayUrl}/api/:path*`,
      },
      {
        source: '/proxy/lms/:path*',
        destination: `${lmsScraperUrl}/api/lms/:path*`,
      },
      {
        source: '/proxy/lms-health',
        destination: `${lmsScraperUrl}/health`,
      },
    ];
  },
};

module.exports = nextConfig;
