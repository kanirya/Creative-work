'use client';

import { useState } from 'react';
import { Button, Input, Card } from '@edupilot/ui';
import { useSubmitQuery } from '@edupilot/api-client';
import { isValidQueryLength } from '@edupilot/utils';
import type { QueryResponseDto } from '@edupilot/types';
import { useOffline } from '@/lib/offline';

export default function QueryPage() {
  const [query, setQuery] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [response, setResponse] = useState<QueryResponseDto | null>(null);
  const [queuedMessage, setQueuedMessage] = useState('');
  const submitQuery = useSubmitQuery();
  const { isOnline, queueQuery } = useOffline();

  const handleTextSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setQueuedMessage('');

    if (!isValidQueryLength(query)) {
      alert('Please enter a valid query (1-1000 characters)');
      return;
    }

    if (!isOnline) {
      queueQuery(query);
      setQueuedMessage('You are offline. Your query has been queued and will be processed when you reconnect.');
      setQuery('');
      return;
    }

    try {
      const result = await submitQuery.mutateAsync({ query, type: 'text' });
      setResponse(result);
    } catch (error) {
      console.error('Query failed:', error);
    }
  };

  const handleVoiceInput = () => {
    if (!isOnline) {
      setQueuedMessage('Voice input is not available offline.');
      return;
    }

    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      alert('Voice input is not supported in your browser');
      return;
    }

    const SpeechRecognition = (window as any).webkitSpeechRecognition || (window as any).SpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.lang = 'en-US';
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onstart = () => setIsRecording(true);

    recognition.onresult = async (event: any) => {
      const transcript = event.results[0][0].transcript;
      setQuery(transcript);
      setIsRecording(false);

      try {
        const result = await submitQuery.mutateAsync({ query: transcript, type: 'voice' });
        setResponse(result);
      } catch (error) {
        console.error('Query failed:', error);
      }
    };

    recognition.onerror = () => {
      setIsRecording(false);
      alert('Voice recognition failed. Please try again.');
    };

    recognition.onend = () => setIsRecording(false);
    recognition.start();
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Ask AI</h1>
        <p className="text-gray-600 mt-2">Ask questions about your courses, assignments, or lecture content</p>
      </div>

      {!isOnline && (
        <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 px-4 py-3 rounded" role="alert">
          You are offline. Queries will be queued and processed when you reconnect.
        </div>
      )}

      {queuedMessage && (
        <div className="bg-blue-50 border border-blue-200 text-blue-800 px-4 py-3 rounded" role="status" aria-live="polite">
          {queuedMessage}
        </div>
      )}

      <Card className="p-6">
        <form onSubmit={handleTextSubmit} className="space-y-4" aria-label="Query submission form">
          <div>
            <label htmlFor="query" className="block text-sm font-medium text-gray-700 mb-2">
              Your Question
            </label>
            <Input
              id="query"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g., What are the key topics in my Data Structures course?"
              disabled={submitQuery.isPending || isRecording}
              className="w-full"
            />
          </div>

          <div className="flex gap-3">
            <Button
              type="submit"
              variant="primary"
              disabled={submitQuery.isPending || isRecording || !query.trim()}
              className="flex-1"
              aria-label={submitQuery.isPending ? 'Processing your query' : 'Submit query'}
            >
              {submitQuery.isPending ? 'Processing...' : isOnline ? 'Submit' : 'Queue Query'}
            </Button>
            <Button
              type="button"
              variant="secondary"
              onClick={handleVoiceInput}
              disabled={submitQuery.isPending || isRecording || !isOnline}
              aria-label={isRecording ? 'Recording voice input' : 'Start voice input'}
            >
              {isRecording ? 'Listening...' : '🎤 Voice'}
            </Button>
          </div>
        </form>
      </Card>

      {response && (
        <Card className="p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Response</h2>
          <div className="prose max-w-none">
            <p className="text-gray-800 whitespace-pre-wrap" aria-live="polite">{response.answer}</p>
          </div>

          {response.confidence !== undefined && (
            <div className="mt-4 pt-4 border-t border-gray-200">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Confidence Score:</span>
                <span className="text-sm font-medium text-gray-900">
                  {(response.confidence * 100).toFixed(0)}%
                </span>
              </div>
              <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all"
                  style={{ width: `${response.confidence * 100}%` }}
                />
              </div>
            </div>
          )}

          {response.sources && response.sources.length > 0 && (
            <div className="mt-6 pt-4 border-t border-gray-200">
              <h3 className="text-sm font-semibold text-gray-900 mb-3">Sources</h3>
              <ul className="space-y-2">
                {response.sources.map((source, index) => (
                  <li key={index} className="text-sm text-gray-600">
                    <span className="font-medium text-gray-900">•</span> {source.title}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </Card>
      )}

      {submitQuery.isError && (
        <Card className="p-6 bg-red-50 border-red-200">
          <p className="text-red-700">Failed to process your query. Please try again.</p>
        </Card>
      )}
    </div>
  );
}
