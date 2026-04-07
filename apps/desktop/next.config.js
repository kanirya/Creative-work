/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  transpilePackages: ['@edupilot/ui', '@edupilot/types', '@edupilot/api-client', '@edupilot/utils'],
  distDir: '.next',
  images: {
    unoptimized: true,
  },
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000',
    NEXT_PUBLIC_LMS_SCRAPER_URL: process.env.NEXT_PUBLIC_LMS_SCRAPER_URL || 'http://localhost:8002',
  },
  // Proxy /api/lms/* to the lms-scraper service to avoid CORS issues
  async rewrites() {
    return [
      {
        source: '/proxy/lms/:path*',
        destination: 'http://localhost:8002/api/lms/:path*',
      },
    ];
  },
};

module.exports = nextConfig;
