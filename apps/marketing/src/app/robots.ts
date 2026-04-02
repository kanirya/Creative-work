import { MetadataRoute } from 'next';

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: '*',
        allow: '/',
        disallow: ['/register', '/api/', '/admin/'],
      },
    ],
    sitemap: 'https://edupilot.com/sitemap.xml',
  };
}
