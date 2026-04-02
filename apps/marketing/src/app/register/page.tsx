'use client';

import { useState } from 'react';

export default function RegisterPage() {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    university: '',
    studentId: '',
  });
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      // TODO: Submit to API Gateway
      await new Promise((resolve) => setTimeout(resolve, 1000));
      setSubmitted(true);
    } catch (err) {
      setError('Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  if (submitted) {
    return (
      <main className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
        <div className="max-w-md w-full bg-white p-8 rounded-lg shadow-md text-center">
          <div className="text-6xl mb-4">✅</div>
          <h1 className="text-2xl font-bold text-gray-900 mb-4">
            Registration Successful!
          </h1>
          <p className="text-gray-600 mb-6">
            Thank you for registering. We'll send you an email with instructions to get started.
          </p>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen flex items-center justify-center bg-gray-50 px-4 py-12">
      <div className="max-w-md w-full bg-white p-8 rounded-lg shadow-md">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Get Started</h1>
        <p className="text-gray-600 mb-8">Create your EduPilot account</p>

        <form onSubmit={handleSubmit} className="space-y-6">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          )}

          <div>
            <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
              Full Name
            </label>
            <input
              id="name"
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full border border-gray-300 rounded-md px-4 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
              disabled={loading}
            />
          </div>

          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
              Email Address
            </label>
            <input
              id="email"
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              className="w-full border border-gray-300 rounded-md px-4 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
              disabled={loading}
            />
          </div>

          <div>
            <label htmlFor="university" className="block text-sm font-medium text-gray-700 mb-2">
              University
            </label>
            <input
              id="university"
              type="text"
              value={formData.university}
              onChange={(e) => setFormData({ ...formData, university: e.target.value })}
              className="w-full border border-gray-300 rounded-md px-4 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
              disabled={loading}
            />
          </div>

          <div>
            <label htmlFor="studentId" className="block text-sm font-medium text-gray-700 mb-2">
              Student ID
            </label>
            <input
              id="studentId"
              type="text"
              value={formData.studentId}
              onChange={(e) => setFormData({ ...formData, studentId: e.target.value })}
              className="w-full border border-gray-300 rounded-md px-4 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
              disabled={loading}
            />
          </div>

          <button
            type="submit"
            className="w-full bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors disabled:opacity-50"
            disabled={loading}
          >
            {loading ? 'Creating Account...' : 'Create Account'}
          </button>
        </form>

        <p className="text-sm text-gray-600 text-center mt-6">
          Already have an account?{' '}
          <a href="/login" className="text-blue-600 hover:text-blue-700 font-medium">
            Sign in
          </a>
        </p>
      </div>
    </main>
  );
}
