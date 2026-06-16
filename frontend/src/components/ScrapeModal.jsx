import { useState } from 'react';
import { api } from '../api';

export default function ScrapeModal({ onClose, onSuccess }) {
  const [maxPages, setMaxPages] = useState(3);
  const [useSelenium, setUseSelenium] = useState(false);
  const [generateInsights, setGenerateInsights] = useState(true);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const handleScrape = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await api.scrapeBooks({ max_pages: maxPages, use_selenium: useSelenium, generate_insights: generateInsights });
      setResult(data);
      onSuccess?.();
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-slate-800 border border-slate-700 rounded-2xl p-6 max-w-md w-full shadow-2xl">
        <h2 className="text-xl font-bold text-white mb-1">Scrape Books</h2>
        <p className="text-slate-400 text-sm mb-6">
          Automatically scrape books from <span className="text-blue-400">books.toscrape.com</span> using Selenium/Requests.
        </p>

        {!result ? (
          <>
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-slate-300 mb-1">Pages to scrape (20 books/page)</label>
                <input
                  type="number" min="1" max="10" value={maxPages}
                  onChange={e => setMaxPages(parseInt(e.target.value))}
                  className="w-full bg-slate-700 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm focus:ring-2 focus:ring-blue-500 outline-none"
                />
              </div>
              <label className="flex items-center gap-3 cursor-pointer">
                <div
                  onClick={() => setUseSelenium(!useSelenium)}
                  className={`w-10 h-5 rounded-full transition-colors ${useSelenium ? 'bg-blue-600' : 'bg-slate-600'}`}
                >
                  <div className={`w-4 h-4 bg-white rounded-full m-0.5 transition-transform ${useSelenium ? 'translate-x-5' : ''}`} />
                </div>
                <span className="text-sm text-slate-300">Use Selenium (headless Chrome)</span>
              </label>
              <label className="flex items-center gap-3 cursor-pointer">
                <div
                  onClick={() => setGenerateInsights(!generateInsights)}
                  className={`w-10 h-5 rounded-full transition-colors ${generateInsights ? 'bg-blue-600' : 'bg-slate-600'}`}
                >
                  <div className={`w-4 h-4 bg-white rounded-full m-0.5 transition-transform ${generateInsights ? 'translate-x-5' : ''}`} />
                </div>
                <span className="text-sm text-slate-300">Generate AI insights</span>
              </label>
            </div>

            {error && <p className="mt-4 text-red-400 text-sm bg-red-900/20 p-3 rounded-lg">{error}</p>}

            <div className="flex gap-3 mt-6">
              <button onClick={onClose} className="flex-1 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm transition-colors">
                Cancel
              </button>
              <button
                onClick={handleScrape} disabled={loading}
                className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-2"
              >
                {loading ? (
                  <><div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" /> Scraping...</>
                ) : 'Start Scraping'}
              </button>
            </div>
          </>
        ) : (
          <div>
            <div className="bg-green-900/30 border border-green-700 rounded-xl p-4 mb-4">
              <p className="text-green-400 font-semibold mb-2">✓ Scraping Complete!</p>
              <div className="text-sm text-slate-300 space-y-1">
                <p>📚 Total scraped: <strong>{result.total_scraped}</strong></p>
                <p>✨ Created: <strong>{result.created}</strong></p>
                <p>🔄 Updated: <strong>{result.updated}</strong></p>
              </div>
            </div>
            {result.errors?.length > 0 && (
              <div className="bg-yellow-900/20 border border-yellow-700 rounded-lg p-3 mb-4">
                <p className="text-yellow-400 text-xs font-medium mb-1">Warnings ({result.errors.length}):</p>
                {result.errors.slice(0, 3).map((e, i) => <p key={i} className="text-yellow-500/70 text-xs">{e}</p>)}
              </div>
            )}
            <button onClick={onClose} className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors">
              Close & Refresh
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
