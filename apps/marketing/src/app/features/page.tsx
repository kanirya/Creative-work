import type { Metadata } from 'next';
import { pageSEO, generateBreadcrumbSchema } from '@/lib/seo';

export const metadata: Metadata = {
  title: pageSEO.features.title,
  description: pageSEO.features.description,
  keywords: pageSEO.features.keywords,
  openGraph: {
    title: pageSEO.features.title,
    description: pageSEO.features.description,
    type: 'website',
    url: 'https://edupilot.com/features',
  },
  twitter: {
    card: 'summary_large_image',
    title: pageSEO.features.title,
    description: pageSEO.features.description,
  },
  alternates: {
    canonical: 'https://edupilot.com/features',
  },
};

const breadcrumbSchema = generateBreadcrumbSchema([
  { name: 'Home', url: 'https://edupilot.com' },
  { name: 'Features', url: 'https://edupilot.com/features' },
]);

export default function FeaturesPage() {
  const features = [
    {
      icon: '🤖',
      title: 'AI-Powered Q&A',
      description: 'Ask questions in natural language and get instant answers from your course materials, lecture recordings, and assignments.',
    },
    {
      icon: '🎥',
      title: 'Automatic Transcription',
      description: 'Lecture recordings are automatically transcribed with timestamps, making it easy to search and review specific topics.',
    },
    {
      icon: '🔍',
      title: 'Semantic Search',
      description: 'Advanced vector search finds relevant information even when you don\'t use exact keywords.',
    },
    {
      icon: '📱',
      title: 'Multi-Platform Access',
      description: 'Access EduPilot on web, desktop (Windows, macOS, Linux), and mobile (iOS, Android).',
    },
    {
      icon: '🔄',
      title: 'LMS Integration',
      description: 'Automatically sync courses, assignments, grades, and announcements from your university LMS.',
    },
    {
      icon: '📊',
      title: 'Dashboard Overview',
      description: 'See all your courses, upcoming assignments, and recent announcements in one place.',
    },
    {
      icon: '🎤',
      title: 'Voice Queries',
      description: 'Ask questions using your voice for hands-free studying.',
    },
    {
      icon: '🔔',
      title: 'Smart Notifications',
      description: 'Get notified about assignment deadlines and important announcements.',
    },
    {
      icon: '💾',
      title: 'Offline Support',
      description: 'Desktop app works offline and queues queries for when you reconnect.',
    },
  ];

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify(breadcrumbSchema),
        }}
      />
      <main>
      <section className="bg-gradient-to-b from-blue-50 to-white py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
              Powerful Features for Modern Students
            </h1>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Everything you need to study smarter, not harder
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <div key={index} className="bg-white p-6 rounded-lg shadow-md">
                <div className="text-4xl mb-4">{feature.icon}</div>
                <h3 className="text-xl font-semibold text-gray-900 mb-3">
                  {feature.title}
                </h3>
                <p className="text-gray-600">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </main>
    </>
  );
}
