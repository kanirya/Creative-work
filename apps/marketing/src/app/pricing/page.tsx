import type { Metadata } from 'next';
import Link from 'next/link';
import { pageSEO, generateBreadcrumbSchema } from '@/lib/seo';

export const metadata: Metadata = {
  title: pageSEO.pricing.title,
  description: pageSEO.pricing.description,
  keywords: pageSEO.pricing.keywords,
  openGraph: {
    title: pageSEO.pricing.title,
    description: pageSEO.pricing.description,
    type: 'website',
    url: 'https://edupilot.com/pricing',
  },
  twitter: {
    card: 'summary_large_image',
    title: pageSEO.pricing.title,
    description: pageSEO.pricing.description,
  },
  alternates: {
    canonical: 'https://edupilot.com/pricing',
  },
};

const breadcrumbSchema = generateBreadcrumbSchema([
  { name: 'Home', url: 'https://edupilot.com' },
  { name: 'Pricing', url: 'https://edupilot.com/pricing' },
]);

const offerSchema = {
  '@context': 'https://schema.org',
  '@type': 'Product',
  name: 'EduPilot',
  description: 'AI-powered study assistant for students',
  offers: [
    {
      '@type': 'Offer',
      name: 'Free Plan',
      price: '0',
      priceCurrency: 'USD',
      availability: 'https://schema.org/InStock',
    },
    {
      '@type': 'Offer',
      name: 'Pro Plan',
      price: '9.99',
      priceCurrency: 'USD',
      availability: 'https://schema.org/InStock',
    },
    {
      '@type': 'Offer',
      name: 'Premium Plan',
      price: '19.99',
      priceCurrency: 'USD',
      availability: 'https://schema.org/InStock',
    },
  ],
};

export default function PricingPage() {
  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify(breadcrumbSchema),
        }}
      />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify(offerSchema),
        }}
      />
      <main>
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
              Simple, Transparent Pricing
            </h1>
            <p className="text-xl text-gray-600">
              Choose the plan that works best for you
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            {/* Free Plan */}
            <div className="bg-white p-8 rounded-lg shadow-md border-2 border-gray-200">
              <h3 className="text-2xl font-bold text-gray-900 mb-2">Free</h3>
              <div className="mb-6">
                <span className="text-4xl font-bold">$0</span>
                <span className="text-gray-600">/month</span>
              </div>
              <ul className="space-y-3 mb-8">
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">✓</span>
                  <span className="text-gray-600">50 AI queries per month</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">✓</span>
                  <span className="text-gray-600">Basic LMS integration</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">✓</span>
                  <span className="text-gray-600">Web access</span>
                </li>
              </ul>
              <Link
                href="/register"
                className="block text-center bg-gray-100 text-gray-900 px-6 py-3 rounded-lg font-semibold hover:bg-gray-200 transition-colors"
              >
                Get Started
              </Link>
            </div>

            {/* Pro Plan */}
            <div className="bg-white p-8 rounded-lg shadow-xl border-2 border-blue-600 relative">
              <div className="absolute top-0 right-0 bg-blue-600 text-white px-3 py-1 text-sm font-semibold rounded-bl-lg">
                Popular
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-2">Pro</h3>
              <div className="mb-6">
                <span className="text-4xl font-bold">$9.99</span>
                <span className="text-gray-600">/month</span>
              </div>
              <ul className="space-y-3 mb-8">
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">✓</span>
                  <span className="text-gray-600">Unlimited AI queries</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">✓</span>
                  <span className="text-gray-600">Full LMS integration</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">✓</span>
                  <span className="text-gray-600">Lecture transcription</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">✓</span>
                  <span className="text-gray-600">Desktop & mobile apps</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">✓</span>
                  <span className="text-gray-600">Priority support</span>
                </li>
              </ul>
              <Link
                href="/register"
                className="block text-center bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors"
              >
                Start Free Trial
              </Link>
            </div>

            {/* Enterprise Plan */}
            <div className="bg-white p-8 rounded-lg shadow-md border-2 border-gray-200">
              <h3 className="text-2xl font-bold text-gray-900 mb-2">Enterprise</h3>
              <div className="mb-6">
                <span className="text-4xl font-bold">Custom</span>
              </div>
              <ul className="space-y-3 mb-8">
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">✓</span>
                  <span className="text-gray-600">Everything in Pro</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">✓</span>
                  <span className="text-gray-600">Custom integrations</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">✓</span>
                  <span className="text-gray-600">Dedicated support</span>
                </li>
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">✓</span>
                  <span className="text-gray-600">SLA guarantees</span>
                </li>
              </ul>
              <Link
                href="/contact"
                className="block text-center bg-gray-100 text-gray-900 px-6 py-3 rounded-lg font-semibold hover:bg-gray-200 transition-colors"
              >
                Contact Sales
              </Link>
            </div>
          </div>
        </div>
      </section>
    </main>
    </>
  );
}
