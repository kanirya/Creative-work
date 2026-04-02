import Link from 'next/link';

export function Navigation() {
  return (
    <nav className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <Link href="/" className="text-2xl font-bold text-blue-600">
            EduPilot
          </Link>
          <div className="hidden md:flex space-x-8">
            <Link href="/" className="text-gray-700 hover:text-gray-900">
              Home
            </Link>
            <Link href="/features" className="text-gray-700 hover:text-gray-900">
              Features
            </Link>
            <Link href="/pricing" className="text-gray-700 hover:text-gray-900">
              Pricing
            </Link>
            <Link href="/about" className="text-gray-700 hover:text-gray-900">
              About
            </Link>
          </div>
          <div className="flex space-x-4">
            <Link
              href="/register"
              className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors"
            >
              Get Started
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
}
