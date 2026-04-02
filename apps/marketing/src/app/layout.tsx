import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { Navigation } from '@/components/Navigation';
import { Footer } from '@/components/Footer';

const inter = Inter({ 
  subsets: ['latin'],
  display: 'swap',
});

export const metadata: Metadata = {
  title: 'EduPilot - AI-Powered Study Assistant for Students',
  description: 'Transform your learning experience with EduPilot. Get instant answers from your course materials, lecture recordings, and assignments using AI.',
  keywords: 'AI study assistant, education technology, student learning, lecture transcription, course management',
  openGraph: {
    title: 'EduPilot - AI-Powered Study Assistant',
    description: 'Transform your learning experience with AI-powered study assistance',
    type: 'website',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <Navigation />
        {children}
        <Footer />
      </body>
    </html>
  );
}
