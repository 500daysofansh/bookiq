import { useState, useEffect, useRef } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { api } from '../api';
import { PaperAirplaneIcon, BookOpenIcon, ClockIcon } from '@heroicons/react/24/outline';
import { SparklesIcon } from '@heroicons/react/24/solid';

const SAMPLE_QUESTIONS = [
  'What science fiction books do you have?',
  'Recommend books similar to 1984',
  'What are the highest-rated mystery books?',
  'Tell me about books by Orwell',
  'Which self-help books would you recommend?',
  'What fantasy novels are available?',
];

function Message({ msg }) {
  if (msg.role === 'user') {
    return (
      <div className="flex justify-end">
        <div className="max-w-[80%] bg-blue-600 text-white rounded-2xl rounded-br-sm px-4 py-3 text-sm">
          {msg.content}
        </div>
      </div>
    );
  }

  return (
    <div className="flex gap-3 items-start">
      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center flex-shrink-0 mt-0.5">
        <SparklesIcon className="h-4 w-4 text-white" />
      </div>
      <div className="flex-1 space-y-3">
        {msg.loading ? (
          <div className="flex gap-1 py-3 px-4 bg-slate-800 rounded-2xl rounded-bl-sm w-fit">
            <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
            <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
            <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
          </div>
        ) : (
          <>
            <div className="bg-slate-800 border border-slate-700 rounded-2xl rounded-bl-sm px-4 py-3 text-sm text-slate-200 leading-relaxed whitespace-pre-wrap">
              {msg.content}
            </div>
            {msg.sources?.length > 0 && (
              <div className="flex flex-wrap gap-2">
                <span className="text-xs text-slate-500">Sources:</span>
                {msg.sources.map((s) => (
                  <Link
                    key={s.book_id}
                    to={`/books/${s.book_id}`}
                    className="flex items-center gap-1.5 text-xs bg-slate-800 hover:bg-slate-700 border border-slate-600 text-blue-400 hover:text-blue-300 px-2.5 py-1 rounded-full transition-colors"
                  >
                    <BookOpenIcon className="h-3 w-3" />
                    {s.title}
                  </Link>
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

export default function AskAI() {
  const [searchParams] = useSearchParams();
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: "Hi! I'm BookIQ, your AI book assistant. I can answer questions about books in the library, give recommendations, and help you find your next great read. What would you like to know?",
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState([]);
  const [showHistory, setShowHistory] = useState(false);
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  // Pre-fill from URL param (from book detail "Ask about this book")
  useEffect(() => {
    const book = searchParams.get('book');
    if (book) setInput(`Tell me about "${book}"`);
  }, [searchParams]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    api.getChatHistory().then(setHistory).catch(() => {});
  }, []);

  const sendMessage = async (question) => {
    const q = (question || input).trim();
    if (!q || loading) return;

    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: q }]);
    setLoading(true);

    // Add loading placeholder
    setMessages(prev => [...prev, { role: 'assistant', loading: true, content: '' }]);

    try {
      const data = await api.askQuestion(q);
      setMessages(prev => {
        const without = prev.filter(m => !m.loading);
        return [...without, {
          role: 'assistant',
          content: data.answer,
          sources: data.sources || [],
          chunks_used: data.chunks_used,
        }];
      });
      // Refresh history
      api.getChatHistory().then(setHistory).catch(() => {});
    } catch (e) {
      setMessages(prev => {
        const without = prev.filter(m => !m.loading);
        return [...without, {
          role: 'assistant',
          content: `Sorry, I encountered an error: ${e.message}. Make sure the backend is running and your OpenRouter API key is configured.`,
          sources: [],
        }];
      });
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col" style={{ height: 'calc(100vh - 64px)' }}>
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <div className="hidden lg:flex flex-col w-72 bg-slate-900 border-r border-slate-700 p-4 gap-4">
          <div>
            <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Sample Questions</h3>
            <div className="space-y-2">
              {SAMPLE_QUESTIONS.map((q, i) => (
                <button
                  key={i}
                  onClick={() => sendMessage(q)}
                  disabled={loading}
                  className="w-full text-left text-xs text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 border border-slate-700 hover:border-slate-500 rounded-lg px-3 py-2.5 transition-all disabled:opacity-50"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>

          {history.length > 0 && (
            <div className="flex-1 overflow-hidden">
              <button
                onClick={() => setShowHistory(!showHistory)}
                className="flex items-center gap-2 text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3 hover:text-slate-300"
              >
                <ClockIcon className="h-3.5 w-3.5" />
                Chat History ({history.length})
              </button>
              {showHistory && (
                <div className="space-y-2 overflow-y-auto max-h-60">
                  {history.map((h) => (
                    <button
                      key={h.id}
                      onClick={() => sendMessage(h.question)}
                      className="w-full text-left text-xs text-slate-400 hover:text-slate-200 bg-slate-800/50 hover:bg-slate-800 rounded-lg px-3 py-2 transition-colors"
                    >
                      <p className="line-clamp-2">{h.question}</p>
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Chat area */}
        <div className="flex-1 flex flex-col">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-4 py-6 space-y-4">
            <div className="max-w-3xl mx-auto space-y-4">
              {messages.map((msg, i) => (
                <Message key={i} msg={msg} />
              ))}
              <div ref={bottomRef} />
            </div>
          </div>

          {/* Input area */}
          <div className="border-t border-slate-700 bg-slate-900/80 backdrop-blur-sm p-4">
            <div className="max-w-3xl mx-auto">
              {/* Mobile sample questions */}
              <div className="flex gap-2 overflow-x-auto pb-2 mb-3 lg:hidden">
                {SAMPLE_QUESTIONS.slice(0, 3).map((q, i) => (
                  <button
                    key={i}
                    onClick={() => sendMessage(q)}
                    disabled={loading}
                    className="flex-shrink-0 text-xs text-slate-300 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-full px-3 py-1.5 transition-colors disabled:opacity-50 whitespace-nowrap"
                  >
                    {q}
                  </button>
                ))}
              </div>

              <div className="flex gap-3 items-end">
                <textarea
                  ref={inputRef}
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Ask anything about the books… (Enter to send)"
                  rows={1}
                  disabled={loading}
                  className="flex-1 bg-slate-800 border border-slate-700 focus:border-blue-500 rounded-2xl px-4 py-3 text-white placeholder-slate-500 text-sm outline-none resize-none transition-colors disabled:opacity-50"
                  style={{ minHeight: '48px', maxHeight: '120px' }}
                />
                <button
                  onClick={() => sendMessage()}
                  disabled={loading || !input.trim()}
                  className="flex-shrink-0 w-12 h-12 bg-blue-600 hover:bg-blue-700 disabled:opacity-40 text-white rounded-2xl flex items-center justify-center transition-colors"
                >
                  {loading
                    ? <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    : <PaperAirplaneIcon className="h-5 w-5" />
                  }
                </button>
              </div>
              <p className="text-xs text-slate-600 text-center mt-2">
                Powered by RAG pipeline • OpenRouter (meta-llama/llama-3.1-8b-instruct:free)
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
