'use client';

import { useState } from 'react';
import { Card, Button } from '@edupilot/ui';
import { isValidQueryLength } from '@edupilot/utils';
import { useOffline } from '@/lib/offline';

interface QueryResponse {
  answer: string;
  confidence?: number;
  sources?: { title: string }[];
}

export default function QueryPage() {
  const [query, setQuery] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [response, setResponse] = useState<QueryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [queuedMsg, setQueuedMsg] = useState('');
  const { isOnline, queueQuery } = useOffline();

  const submitQuery = async (text: string) => {
    if (!isValidQueryLength(text)) {
      setError('Please enter a valid query (1-1000 characters)');
      return;
    }

    if (!isOnline) {
      queueQuery(text);
      setQueuedMsg('You are offline. Your query has been queued and will be processed when you reconnect.');
      setQuery('');
      return;
    }

    setLoading(true);
    setError('');
    setQueuedMsg('');

    try {
      // Call the LMS scraper's AI query endpoint via proxy
      const res = await fetch('/proxy/lms/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: text, type: 'text' }),
      });

      if (!res.ok) {
        // Fallback: return a helpful message based on scraped data
        setResponse({
          answer: `I searched your LMS data for: "${text}"\n\nThe AI query service is not available right now. Your courses, grades, and assignments are available in the sidebar navigation.`,
          confidence: 0.5,
          sources: [],
        });
        return;
      }

      const data = await res.json();
      setResponse(data);
    } catch {
      // Graceful fallback
      setResponse({
        answer: `I searched your LMS data for: "${text}"\n\nThe AI query service is not available right now. Please check your courses, grades, and assignments using the sidebar navigation.`,
        confidence: 0.5,
        sources: [],
      });
    } finally {
      setLoading(false);
    }
  };

  const handleTextSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await submitQuery(query);
  };

  const handleVoiceInput = () => {
    if (!isOnline) { setQueuedMsg('Voice input is not available offline.'); return; }
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      setError('Voice input is not supported in your browser');
      return;
    }
    const SR = (window as any).webkitSpeechRecognition || (window as any).SpeechRecognition;
    const recognition = new SR();
    recognition.lang = 'en-US';
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.onstart = () => setIsRecording(true);
    recognition.onresult = async (event: any) => {
      const transcript = event.results[0][0].transcript;
      setQuery(transcript);
      setIsRecording(false);
      await submitQuery(transcript);
    };
    recognition.onerror = () => { setIsRecording(false); setError('Voice recognition failed.'); };
    recognition.onend = () => setIsRecording(false);
    recognition.start();
  };

  return (
    <div className="p-8 max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Ask AI</h1>
        <p className="text-gray-600 mt-2 text-sm">Ask questions about your courses, assignments, or grades</p>
      </div>

      {!isOnline && (
        <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 px-4 py-3 rounded text-sm" role="alert">
          You are offline. Queries will be queued and processed when you reconnect.
        </div>
      )}

      {queuedMsg && (
        <div className="bg-blue-50 border border-blue-200 text-blue-800 px-4 py-3 rounded text-sm" role="status" aria-live="polite">
          {queuedMsg}
        </div>
      )}

      <Card className="p-6">
        <form onSubmit={handleTextSubmit} className="space-y-4" aria-label="Query form">
          <div>
            <label htmlFor="query" className="block text-sm font-medium text-gray-700 mb-1.5">
              Your Question
            </label>
            <input
              id="query"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g., What are my upcoming assignments? What is my grade in Database Systems?"
              disabled={loading || isRecording}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {error && <p className="text-red-600 text-sm">{error}</p>}

          <div className="flex gap-3">
            <Button
              type="submit"
              variant="primary"
              disabled={loading || isRecording || !query.trim()}
              className="flex-1"
            >
              {loading ? 'Processing...' : isOnline ? 'Submit' : 'Queue Query'}
            </Button>
            <Button
              type="button"
              variant="secondary"
              onClick={handleVoiceInput}
              disabled={loading || isRecording || !isOnline}
            >
              {isRecording ? '🔴 Listening...' : '🎤 Voice'}
            </Button>
          </div>
        </form>
      </Card>

      {response && (
        <Card className="p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-3">Response</h2>
          <p className="text-gray-800 whitespace-pre-wrap text-sm" aria-live="polite">{response.answer}</p>

          {response.confidence !== undefined && (
            <div className="mt-4 pt-4 border-t border-gray-100">
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-500">Confidence:</span>
                <span className="font-medium">{(response.confidence * 100).toFixed(0)}%</span>
              </div>
              <div className="mt-1.5 w-full bg-gray-200 rounded-full h-1.5">
                <div className="bg-blue-600 h-1.5 rounded-full" style={{ width: `${response.confidence * 100}%` }} />
              </div>
            </div>
          )}

          {response.sources && response.sources.length > 0 && (
            <div className="mt-4 pt-4 border-t border-gray-100">
              <p className="text-sm font-medium text-gray-700 mb-2">Sources</p>
              <ul className="space-y-1">
                {response.sources.map((s, i) => (
                  <li key={i} className="text-sm text-gray-600">• {s.title}</li>
                ))}
              </ul>
            </div>
          )}
        </Card>
      )}
    </div>
  );
}
