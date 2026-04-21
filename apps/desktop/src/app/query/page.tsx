'use client';

import { FormEvent, useMemo, useState } from 'react';
import { Card, Button } from '@edupilot/ui';
import { isValidQueryLength } from '@edupilot/utils';
import { lmsApi, LMSQueryResponse } from '@/lib/lms-api';
import { useOffline } from '@/lib/offline';

type MessageRole = 'user' | 'assistant';

interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  confidence?: number;
  sources?: LMSQueryResponse['sources'];
}

function buildAssistantMessage(response: LMSQueryResponse): ChatMessage {
  return {
    id: crypto.randomUUID(),
    role: 'assistant',
    content: response.answer,
    confidence: response.confidence,
    sources: response.sources,
  };
}

export default function QueryPage() {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [queuedMsg, setQueuedMsg] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content:
        'Ask me anything about your courses, assignments, deadlines, grades, or upcoming LMS activity. I will answer from your synced academic data.',
    },
  ]);
  const { isOnline, queueQuery } = useOffline();

  const suggestions = useMemo(
    () => [
      'What assignments are due next?',
      'Which course needs my attention most right now?',
      'Summarize my current academic status.',
      'Do I have anything I can submit right now?',
    ],
    []
  );

  const submitQuery = async (text: string) => {
    const trimmed = text.trim();
    if (!isValidQueryLength(trimmed)) {
      setError('Please enter a valid question between 1 and 1000 characters.');
      return;
    }

    if (!isOnline) {
      queueQuery(trimmed);
      setQueuedMsg('You are offline. Your question has been queued for later.');
      setQuery('');
      return;
    }

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content: trimmed,
    };

    setMessages((current) => [...current, userMessage]);
    setLoading(true);
    setError('');
    setQueuedMsg('');
    setQuery('');

    try {
      const response = await lmsApi.queryAI(trimmed);
      setMessages((current) => [...current, buildAssistantMessage(response)]);
    } catch (err: any) {
      setError(err?.message || 'AI is unavailable right now.');
      setMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: 'assistant',
          content:
            'I could not complete that request right now. Please make sure your LMS is synced and the AI service is configured.',
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    await submitQuery(query);
  };

  return (
    <div className="app-page flex min-h-[calc(100vh-2rem)] flex-col gap-5">
      <section className="section-card flex items-start justify-between gap-4 px-6 py-5">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-400">AI Study Copilot</p>
          <h1 className="mt-3 text-3xl font-semibold tracking-tight text-slate-950">Ask EduPilot AI</h1>
          <p className="mt-2 max-w-3xl text-sm leading-7 text-slate-500">
            A real OpenAI-backed chat over your live LMS session. Ask about deadlines, submissions, grades, and academic workload in natural language.
          </p>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-medium text-slate-500">
          Live LMS context
        </div>
      </section>

      {!isOnline && (
        <div className="rounded-[20px] border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          You are offline. Questions will be queued until you reconnect.
        </div>
      )}

      {queuedMsg && (
        <div className="rounded-[20px] border border-blue-200 bg-blue-50 px-4 py-3 text-sm text-blue-800">
          {queuedMsg}
        </div>
      )}

      {error && (
        <div className="rounded-[20px] border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      <div className="grid min-h-0 flex-1 items-start gap-5 xl:grid-cols-[minmax(0,1fr)_300px]">
        <Card className="section-card flex min-h-[620px] flex-col overflow-hidden">
          <div className="min-h-0 flex-1 space-y-4 overflow-y-auto pr-1">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[85%] rounded-[24px] px-4 py-3.5 text-sm leading-7 ${
                    message.role === 'user'
                      ? 'bg-slate-950 text-white'
                      : 'border border-slate-200 bg-white text-slate-800'
                  }`}
                >
                  <p className="whitespace-pre-wrap">{message.content}</p>

                  {message.role === 'assistant' && message.confidence !== undefined && (
                    <div className="mt-3 border-t border-slate-100 pt-3">
                      <div className="flex items-center justify-between text-xs text-slate-500">
                        <span>Confidence</span>
                        <span className="font-medium text-slate-700">
                          {(message.confidence * 100).toFixed(0)}%
                        </span>
                      </div>
                      <div className="mt-2 h-1.5 w-full rounded-full bg-slate-100">
                        <div
                          className="h-1.5 rounded-full bg-slate-900"
                          style={{ width: `${message.confidence * 100}%` }}
                        />
                      </div>
                    </div>
                  )}

                  {message.role === 'assistant' && message.sources && message.sources.length > 0 && (
                    <div className="mt-3 border-t border-slate-100 pt-3">
                      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Sources</p>
                      <div className="mt-2 flex flex-wrap gap-2">
                        {message.sources.map((source, index) => (
                          <a
                            key={`${source.title}-${index}`}
                            href={source.url || '#'}
                            target={source.url ? '_blank' : undefined}
                            rel={source.url ? 'noreferrer' : undefined}
                            className={`rounded-full border px-3 py-1.5 text-xs ${
                              source.url
                                ? 'border-slate-200 bg-slate-50 text-slate-700 hover:border-slate-300 hover:bg-white'
                                : 'border-slate-100 bg-slate-50 text-slate-500'
                            }`}
                          >
                            {source.title}
                          </a>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}

            {loading && (
              <div className="flex justify-start">
                <div className="rounded-[24px] border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600">
                  EduPilot AI is thinking...
                </div>
              </div>
            )}
          </div>

          <form onSubmit={handleSubmit} className="mt-5 shrink-0 border-t border-slate-100 pt-5">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
              <textarea
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Ask about assignments, grades, deadlines, course load, or what to study next..."
                disabled={loading}
                rows={3}
                className="min-h-[88px] w-full flex-1 resize-none rounded-[22px] border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-800 outline-none transition focus:border-slate-300 focus:bg-white"
              />
              <Button
                type="submit"
                variant="primary"
                disabled={loading || !query.trim()}
                className="w-full sm:w-auto sm:self-end"
              >
                {loading ? 'Thinking...' : 'Send'}
              </Button>
            </div>
          </form>
        </Card>

        <Card className="section-card sticky top-6 h-fit">
          <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-400">Prompt ideas</p>
          <div className="mt-4 space-y-2.5">
            {suggestions.map((suggestion) => (
              <button
                key={suggestion}
                type="button"
                onClick={() => setQuery(suggestion)}
                className="w-full rounded-[20px] border border-slate-200 bg-slate-50 px-4 py-3 text-left text-sm text-slate-700 transition hover:border-slate-300 hover:bg-white"
              >
                {suggestion}
              </button>
            ))}
          </div>

          <div className="mt-5 rounded-[20px] border border-slate-200 bg-white px-4 py-4 text-sm leading-7 text-slate-500">
            This chat currently answers from synced LMS profile, courses, assignments, grades, and calendar data. The next upgrade is direct course-file and lecture-document ingestion.
          </div>
        </Card>
      </div>
    </div>
  );
}
