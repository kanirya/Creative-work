// SEO utilities and structured data

export interface PageSEO {
  title: string;
  description: string;
  keywords?: string;
  ogImage?: string;
  canonical?: string;
}

export const defaultSEO: PageSEO = {
  title: 'EduPilot - AI-Powered Study Assistant for Students',
  description: 'Transform your learning experience with EduPilot. Get instant answers from your course materials, lecture recordings, and assignments using AI.',
  keywords: 'AI study assistant, education technology, student learning, lecture transcription, course management, LMS integration',
  ogImage: '/og-image.jpg',
};

export const pageSEO = {
  home: {
    title: 'EduPilot - AI-Powered Study Assistant for Students',
    description: 'Transform your learning experience with EduPilot. Get instant answers from your course materials, lecture recordings, and assignments using AI.',
    keywords: 'AI study assistant, education technology, student learning, lecture transcription, course management',
  },
  features: {
    title: 'Features - EduPilot AI Study Assistant',
    description: 'Discover all the powerful features that make EduPilot the best AI study assistant for students. AI-powered Q&A, automatic transcription, LMS integration, and more.',
    keywords: 'AI features, study tools, lecture transcription, semantic search, LMS integration, voice queries',
  },
  pricing: {
    title: 'Pricing - EduPilot Plans & Pricing',
    description: 'Choose the perfect EduPilot plan for your needs. Free for students, with premium features available. No credit card required to start.',
    keywords: 'pricing, student plans, education pricing, free trial, subscription',
  },
  about: {
    title: 'About EduPilot - Our Mission & Story',
    description: 'Learn about EduPilot and our mission to transform education with AI technology. Discover how we help students learn more effectively.',
    keywords: 'about us, mission, education technology, AI learning, student success',
  },
  register: {
    title: 'Register - Get Started with EduPilot',
    description: 'Create your free EduPilot account and start studying smarter today. Join thousands of students already using AI-powered study assistance.',
    keywords: 'sign up, register, create account, free trial, get started',
  },
};

// Organization structured data
export const organizationSchema = {
  '@context': 'https://schema.org',
  '@type': 'Organization',
  name: 'EduPilot by Agentix',
  description: 'AI-powered study assistant for university students',
  url: 'https://edupilot.com',
  logo: 'https://edupilot.com/logo.png',
  sameAs: [
    'https://twitter.com/edupilot',
    'https://linkedin.com/company/edupilot',
  ],
  contactPoint: {
    '@type': 'ContactPoint',
    contactType: 'Customer Support',
    email: 'support@edupilot.com',
  },
};

// Software application structured data
export const softwareApplicationSchema = {
  '@context': 'https://schema.org',
  '@type': 'SoftwareApplication',
  name: 'EduPilot',
  applicationCategory: 'EducationalApplication',
  operatingSystem: 'Web, Windows, macOS, Linux, iOS, Android',
  offers: {
    '@type': 'Offer',
    price: '0',
    priceCurrency: 'USD',
  },
  aggregateRating: {
    '@type': 'AggregateRating',
    ratingValue: '4.8',
    ratingCount: '1250',
  },
  description: 'AI-powered study assistant that helps students get instant answers from course materials, lecture recordings, and assignments.',
  featureList: [
    'AI-powered Q&A',
    'Automatic lecture transcription',
    'LMS integration',
    'Semantic search',
    'Multi-platform support',
    'Voice queries',
  ],
};

// FAQ structured data for homepage
export const faqSchema = {
  '@context': 'https://schema.org',
  '@type': 'FAQPage',
  mainEntity: [
    {
      '@type': 'Question',
      name: 'What is EduPilot?',
      acceptedAnswer: {
        '@type': 'Answer',
        text: 'EduPilot is an AI-powered study assistant that helps students by providing instant answers from their course materials, lecture recordings, and assignments using advanced natural language processing.',
      },
    },
    {
      '@type': 'Question',
      name: 'How does EduPilot work?',
      acceptedAnswer: {
        '@type': 'Answer',
        text: 'EduPilot integrates with your university LMS to sync courses and assignments, transcribes lecture recordings, and uses AI to answer your questions based on your actual course content.',
      },
    },
    {
      '@type': 'Question',
      name: 'Is EduPilot free?',
      acceptedAnswer: {
        '@type': 'Answer',
        text: 'Yes, EduPilot offers a free plan for students with core features. Premium plans with additional features are also available.',
      },
    },
    {
      '@type': 'Question',
      name: 'What platforms does EduPilot support?',
      acceptedAnswer: {
        '@type': 'Answer',
        text: 'EduPilot is available on web browsers, desktop (Windows, macOS, Linux), and mobile devices (iOS and Android).',
      },
    },
  ],
};

// Breadcrumb structured data helper
export function generateBreadcrumbSchema(items: { name: string; url: string }[]) {
  return {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: items.map((item, index) => ({
      '@type': 'ListItem',
      position: index + 1,
      name: item.name,
      item: item.url,
    })),
  };
}
