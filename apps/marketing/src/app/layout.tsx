import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { Navigation } from '@/components/Navigation';
import { Footer } from '@/components/Footer';
import { organizationSchema } from '@/lib/seo';

const inter = Inter({ 
  subsets: ['latin'],
  display: 'swap',
});

export const metadata: Metadata = {
  metadataBase: new URL('https://edupilot.com'),
  title: {
    default: 'EduPilot - AI-Powered Study Assistant for Students',
    template: '%s | EduPilot',
  },
  description: 'Transform your learning experience with EduPilot. Get instant answers from your course materials, lecture recordings, and assignments using AI.',
  keywords: ['AI study assistant', 'education technology', 'student learning', 'lecture transcription', 'course management', 'LMS integration', 'semantic search'],
  authors: [{ name: 'Agentix' }],
  creator: 'Agentix',
  publisher: 'Agentix',
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: 'https://edupilot.com',
    siteName: 'EduPilot',
    title: 'EduPilot - AI-Powered Study Assistant',
    description: 'Transform your learning experience with AI-powered study assistance',
    images: [
      {
        url: '/og-image.jpg',
        width: 1200,
        height: 630,
        alt: 'EduPilot - AI Study Assistant',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'EduPilot - AI-Powered Study Assistant',
    description: 'Transform your learning experience with AI-powered study assistance',
    images: ['/og-image.jpg'],
    creator: '@edupilot',
  },
  verification: {
    google: 'google-site-verification-code',
  },
  alternates: {
    canonical: 'https://edupilot.com',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link rel="manifest" href="/manifest.json" />
        <link rel="icon" href="/favicon.ico" sizes="any" />
        <link rel="apple-touch-icon" href="/apple-touch-icon.png" />
        <meta name="theme-color" content="#2563eb" />
        <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=5" />
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify(organizationSchema),
          }}
        />
      </head>
      <body className={inter.className}>
        <Navigation />
        {children}
        <Footer />
      </body>
    </html>
  );
}
