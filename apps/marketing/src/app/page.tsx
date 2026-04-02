import Link from 'next/link';

export default function HomePage() {
  return (
    <main>
      {/* Hero Section */}
      <section className="bg-gradient-to-b from-blue-50 to-white py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h1 className="text-5xl md:text-6xl font-bold text-gray-900 mb-6">
              Your AI Study Assistant
            </h1>
            <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
              Transform your learning experience with EduPilot. Get instant answers from your 
              course materials, lecture recordings, and assignments using advanced AI.
            </p>
            <div className="flex justify-center gap-4">
              <Link
                href="/register"
                className="bg-blue-600 text-white px-8 py-3 rounded-lg text-lg font-semibold hover:bg-blue-700 transition-colors"
              >
                Get Started Free
              </Link>
              <Link
                href="/features"
                className="bg-white text-blue-600 px-8 py-3 rounded-lg text-lg font-semibold border-2 border-blue-600 hover:bg-blue-50 transition-colors"
              >
                Learn More
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-4xl font-bold text-center text-gray-900 mb-12">
            Everything You Need to Excel
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="bg-white p-8 rounded-lg shadow-md">
              <div className="text-4xl mb-4">🤖</div>
              <h3 className="text-xl font-semibold mb-3">AI-Powered Answers</h3>
              <p className="text-gray-600">
                Ask questions about your courses and get instant, accurate answers from your 
                lecture materials and course content.
              </p>
            </div>
            <div className="bg-white p-8 rounded-lg shadow-md">
              <div className="text-4xl mb-4">🎥</div>
              <h3 className="text-xl font-semibold mb-3">Lecture Transcription</h3>
              <p className="text-gray-600">
                Automatically transcribe lecture recordings and search through them to find 
                exactly what you need.
              </p>
            </div>
            <div className="bg-white p-8 rounded-lg shadow-md">
              <div className="text-4xl mb-4">📚</div>
              <h3 className="text-xl font-semibold mb-3">Course Integration</h3>
              <p className="text-gray-600">
                Seamlessly sync with your LMS to access courses, assignments, and grades 
                all in one place.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Demo Section */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-4xl font-bold text-center text-gray-900 mb-12">
            See EduPilot in Action
          </h2>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <h3 className="text-2xl font-semibold text-gray-900 mb-4">
                Ask Questions, Get Instant Answers
              </h3>
              <p className="text-gray-600 mb-6">
                Simply type or speak your question, and EduPilot searches through your 
                course materials, lecture transcriptions, and assignments to provide 
                accurate, contextual answers with source citations.
              </p>
              <div className="bg-white p-6 rounded-lg shadow-md">
                <div className="text-sm text-gray-500 mb-2">Example Query:</div>
                <div className="bg-blue-50 p-4 rounded-md mb-4">
                  <p className="text-gray-900">"What are the main sorting algorithms covered in my Data Structures course?"</p>
                </div>
                <div className="text-sm text-gray-500 mb-2">AI Response:</div>
                <div className="bg-gray-50 p-4 rounded-md">
                  <p className="text-gray-700 text-sm">
                    Based on your Data Structures course materials, the main sorting algorithms 
                    covered are: Bubble Sort, Selection Sort, Insertion Sort, Merge Sort, Quick Sort, 
                    and Heap Sort. These were discussed in Lecture 5 and Assignment 3.
                  </p>
                </div>
              </div>
            </div>
            
            <div className="bg-white p-6 rounded-lg shadow-lg">
              <div className="aspect-video bg-gray-200 rounded-lg flex items-center justify-center mb-4">
                <div className="text-center text-gray-500">
                  <div className="text-6xl mb-2">▶️</div>
                  <p>Demo Video</p>
                </div>
              </div>
              <p className="text-sm text-gray-600 text-center">
                Watch how EduPilot helps students study more effectively
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="bg-blue-600 py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-6">
            Ready to Transform Your Learning?
          </h2>
          <p className="text-xl text-blue-100 mb-8">
            Join thousands of students already using EduPilot
          </p>
          <Link
            href="/register"
            className="bg-white text-blue-600 px-8 py-3 rounded-lg text-lg font-semibold hover:bg-gray-100 transition-colors inline-block"
          >
            Start Your Free Trial
          </Link>
        </div>
      </section>
    </main>
  );
}
