import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'About - EduPilot',
  description: 'Learn about EduPilot and our mission to transform education with AI technology.',
};

export default function AboutPage() {
  return (
    <main>
      <section className="py-20">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-8">
            About EduPilot
          </h1>
          
          <div className="prose prose-lg max-w-none">
            <p className="text-xl text-gray-600 mb-6">
              EduPilot is an AI-powered study assistant designed to help students learn more 
              effectively by providing instant access to their course materials, lecture recordings, 
              and assignments.
            </p>

            <h2 className="text-2xl font-bold text-gray-900 mt-12 mb-4">Our Mission</h2>
            <p className="text-gray-600 mb-6">
              We believe that every student deserves access to powerful learning tools that help 
              them succeed. Our mission is to make education more accessible, efficient, and 
              effective through the power of artificial intelligence.
            </p>

            <h2 className="text-2xl font-bold text-gray-900 mt-12 mb-4">How It Works</h2>
            <p className="text-gray-600 mb-6">
              EduPilot integrates with your university's Learning Management System (LMS) to 
              automatically sync your courses, assignments, and grades. It transcribes lecture 
              recordings and uses advanced AI to answer your questions based on your actual 
              course content.
            </p>

            <h2 className="text-2xl font-bold text-gray-900 mt-12 mb-4">Privacy & Security</h2>
            <p className="text-gray-600 mb-6">
              We take your privacy seriously. All data is encrypted in transit and at rest. 
              We comply with FERPA regulations and never share your academic information with 
              third parties.
            </p>
          </div>
        </div>
      </section>
    </main>
  );
}
