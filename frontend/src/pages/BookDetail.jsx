import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { api } from '../api';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';
import BookCard from '../components/BookCard';
import { StarIcon } from '@heroicons/react/24/solid';
import { ArrowLeftIcon, ExternalLinkIcon } from '@heroicons/react/24/outline';

function StarRow({ rating }) {
  return (
    <div className="flex items-center gap-1">
      {[1,2,3,4,5].map(s => (
        <StarIcon key={s} className={`h-5 w-5 ${s <= Math.round(rating) ? 'text-yellow-400' : 'text-slate-600'}`} />
      ))}
      <span className="text-sm text-slate-400 ml-1">{rating?.toFixed(1)}/5.0</span>
    </div>
  );
}

function Badge({ label, color = 'blue' }) {
  const colors = {
    blue: 'bg-blue-900/50 text-blue-300 border-blue-700',
    green: 'bg-green-900/50 text-green-300 border-green-700',
    purple: 'bg-purple-900/50 text-purple-300 border-purple-700',
    yellow: 'bg-yellow-900/50 text-yellow-300 border-yellow-700',
  };
  return (
    <span className={`inline-block px-3 py-1 rounded-full text-xs font-medium border ${colors[color]}`}>
      {label}
    </span>
  );
}

function SentimentBar({ sentiment, score }) {
  const color = sentiment === 'Positive' ? 'bg-green-500' : sentiment === 'Negative' ? 'bg-red-500' : 'bg-yellow-500';
  return (
    <div>
      <div className="flex justify-between text-xs text-slate-400 mb-1">
        <span>Sentiment: <span className="text-white font-medium">{sentiment}</span></span>
        <span>{Math.round((score || 0.5) * 100)}%</span>
      </div>
      <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
        <div className={`h-full ${color} rounded-full transition-all`} style={{ width: `${(score || 0.5) * 100}%` }} />
      </div>
    </div>
  );
}

export default function BookDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [book, setBook] = useState(null);
  const [recs, setRecs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    setLoading(true);
    Promise.all([
      api.getBook(id),
      api.getRecommendations(id),
    ])
      .then(([bookData, recData]) => {
        setBook(bookData);
        setRecs(recData.recommendations || []);
      })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <LoadingSpinner text="Loading book details…" />;
  if (error) return <ErrorMessage error={error} onRetry={() => window.location.reload()} />;
  if (!book) return null;

  const insight = book.ai_insight || {};
  const themes = (() => { try { return JSON.parse(insight.key_themes || '[]'); } catch { return []; } })();
  const FALLBACK = `https://via.placeholder.com/300x450/1e293b/3b82f6?text=${encodeURIComponent(book.title?.slice(0,12))}`;

  return (
    <div className="min-h-screen bg-slate-950">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Back button */}
        <button
          onClick={() => navigate(-1)}
          className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors mb-8 group"
        >
          <ArrowLeftIcon className="h-4 w-4 group-hover:-translate-x-1 transition-transform" />
          Back to Library
        </button>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-10">
          {/* Left: Cover + meta */}
          <div className="lg:col-span-1 space-y-6">
            <div className="relative">
              <img
                src={book.cover_image_url || FALLBACK}
                alt={book.title}
                onError={e => { e.target.src = FALLBACK; }}
                className="w-full max-w-sm mx-auto rounded-2xl shadow-2xl shadow-blue-900/30 border border-slate-700"
              />
            </div>

            {/* Quick metadata */}
            <div className="bg-slate-800/60 border border-slate-700 rounded-2xl p-5 space-y-3">
              {book.rating != null && <StarRow rating={book.rating} />}
              {book.num_reviews > 0 && (
                <p className="text-sm text-slate-400">{book.num_reviews.toLocaleString()} reviews</p>
              )}
              {book.price && (
                <div className="flex justify-between">
                  <span className="text-slate-400 text-sm">Price</span>
                  <span className="text-green-400 font-bold">{book.price}</span>
                </div>
              )}
              {book.availability && (
                <div className="flex justify-between">
                  <span className="text-slate-400 text-sm">Availability</span>
                  <span className="text-white text-sm">{book.availability}</span>
                </div>
              )}
              {book.book_url && (
                <a
                  href={book.book_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center justify-center gap-2 w-full py-2.5 mt-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-sm font-medium transition-colors"
                >
                  View on Site <span className="text-xs">↗</span>
                </a>
              )}
            </div>
          </div>

          {/* Right: Book info + AI insights */}
          <div className="lg:col-span-2 space-y-6">
            {/* Title block */}
            <div>
              {book.genre && <Badge label={book.genre} color="blue" />}
              <h1 className="text-3xl font-bold text-white mt-3 mb-1 leading-tight">{book.title}</h1>
              <p className="text-lg text-slate-400">by {book.author || 'Unknown Author'}</p>
            </div>

            {/* Description */}
            {book.description && (
              <div className="bg-slate-800/60 border border-slate-700 rounded-2xl p-6">
                <h2 className="text-lg font-semibold text-white mb-3">Description</h2>
                <p className="text-slate-300 leading-relaxed text-sm">{book.description}</p>
              </div>
            )}

            {/* AI Insights */}
            {Object.keys(insight).length > 0 && (
              <div className="bg-gradient-to-br from-blue-900/20 to-purple-900/20 border border-blue-700/40 rounded-2xl p-6 space-y-5">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-lg">🤖</span>
                  <h2 className="text-lg font-semibold text-white">AI Insights</h2>
                  <span className="text-xs bg-blue-600/40 text-blue-300 px-2 py-0.5 rounded-full border border-blue-600/40">
                    Powered by OpenRouter
                  </span>
                </div>

                {/* Summary */}
                {insight.summary && (
                  <div>
                    <h3 className="text-sm font-medium text-slate-400 mb-2 uppercase tracking-wide">📝 Summary</h3>
                    <p className="text-slate-200 text-sm leading-relaxed bg-slate-800/50 rounded-xl p-4 border border-slate-700/50">
                      {insight.summary}
                    </p>
                  </div>
                )}

                {/* Genre classification */}
                {insight.predicted_genre && (
                  <div>
                    <h3 className="text-sm font-medium text-slate-400 mb-2 uppercase tracking-wide">🏷️ AI Genre Classification</h3>
                    <Badge label={insight.predicted_genre} color="purple" />
                  </div>
                )}

                {/* Themes */}
                {themes.length > 0 && (
                  <div>
                    <h3 className="text-sm font-medium text-slate-400 mb-2 uppercase tracking-wide">💡 Key Themes</h3>
                    <div className="flex flex-wrap gap-2">
                      {themes.map((t, i) => <Badge key={i} label={t} color="yellow" />)}
                    </div>
                  </div>
                )}

                {/* Sentiment */}
                {insight.sentiment && (
                  <div>
                    <h3 className="text-sm font-medium text-slate-400 mb-2 uppercase tracking-wide">📊 Sentiment Analysis</h3>
                    <SentimentBar sentiment={insight.sentiment} score={insight.sentiment_score} />
                  </div>
                )}
              </div>
            )}

            {/* Ask about this book */}
            <div className="bg-slate-800/60 border border-slate-700 rounded-2xl p-5">
              <h3 className="text-sm font-medium text-slate-300 mb-3">💬 Have a question about this book?</h3>
              <Link
                to={`/ask?book=${encodeURIComponent(book.title)}`}
                className="inline-flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-sm font-medium transition-colors"
              >
                Ask the AI →
              </Link>
            </div>
          </div>
        </div>

        {/* Recommendations */}
        {recs.length > 0 && (
          <div className="mt-14">
            <h2 className="text-2xl font-bold text-white mb-2">
              📖 If you liked <span className="text-blue-400">{book.title}</span>, you'll like…
            </h2>
            <p className="text-slate-500 text-sm mb-6">AI-powered recommendations based on genre and description similarity</p>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
              {recs.map(rec => <BookCard key={rec.id} book={rec} />)}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
