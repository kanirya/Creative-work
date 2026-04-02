/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'export',
  images: {
    unoptimized: true, // Required for static export
    formats: ['image/avif', 'image/webp'],
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
  },
  // Enable compression
  compress: true,
  // Performance optimizations
  swcMinify: true,
  // Generate ETags for caching
  generateEtags: true,
  // Optimize fonts
  optimizeFonts: true,
  // Trailing slash for better SEO
  trailingSlash: false,
};

module.exports = nextConfig;
