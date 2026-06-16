import { useState, useEffect, useCallback } from 'react';
import { api } from '../api';
import BookCard from '../components/BookCard';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';
import ScrapeModal from '../components/ScrapeModal';
import { MagnifyingGlassIcon, FunnelIcon, ArrowPathIcon, PlusIcon } from '@heroicons/react/24/outline';

export default function Dashboard() {
  const [books, setBooks] = useState([]);
  const [genres, setGenres] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [selectedGenre, setSelectedGenre] = useState('');
  const [sort, setSort] = useState('-rating');
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [showScrapeModal, setShowScrapeModal] = useState(false);

  const fetchBooks = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const params = { sort, page };
      if (search) params.search = search;
      if (selectedGenre) params.genre = selectedGenre;
      const data = await api.getBooks(params);
      setBooks(data.results || data);
      setTotalCount(data.count || (data.results || data).length);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [search, selectedGenre, sort, page]);

  useEffect(() => { fetchBooks(); }, [fetchBooks]);

  useEffect(() => {
    api.getGenres().then(setGenres).catch(() => {});
    api.getStats().then(setStats).catch(() => {});
  }, []);

  const handleSearch = (e) => {
    e.preventDefault();
    setPage(1);
    fetchBooks();
  };

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Hero stats bar */}
      {stats && (
        <div className="bg-gradient-to-r from-blue-900/40 via-slate-900 to-purple-900/40 border-b border-slate-700/50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <div className="flex flex-wrap items-center gap-6">
              <div className="text-center">
                <p className="text-2xl font-bold text-blue-400">{stats.total_books}</p>
                <p className="text-xs text-slate-400">Books</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-purple-400">{stats.total_genres}</p>
                <p className="text-xs text-slate-400">Genres</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-yellow-400">{stats.avg_rating?.toFixed(1) ?? '-'}</p>
                <p className="text-xs text-slate-400">Avg Rating</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-green-400">{stats.total_qa}</p>
                <p className="text-xs text-slate-400">Questions Asked</p>
              </div>
              <div className="ml-auto flex gap-2">
                <button
                  onClick={() => setShowScrapeModal(true)}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors"
                >
                  <ArrowPathIcon className="h-4 w-4" /> Scrape Books
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Search & filters */}
        <div className="flex flex-wrap gap-3 mb-8">
          <form onSubmit={handleSearch} className="flex-1 min-w-[240px] flex gap-2">
            <div className="relative flex-1">
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <input
                type="text"
                placeholder="Search books or authors…"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full bg-slate-800 border border-slate-700 rounded-xl pl-10 pr-4 py-2.5 text-white placeholder-slate-500 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
              />
            </div>
            <button type="submit" className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-sm font-medium transition-colors">
              Search
            </button>
          </form>

          <select
            value={selectedGenre}
            onChange={(e) => { setSelectedGenre(e.target.value); setPage(1); }}
            className="bg-slate-800 border border-slate-700 rounded-xl px-3 py-2.5 text-white text-sm focus:ring-2 focus:ring-blue-500 outline-none"
          >
            <option value="">All Genres</option>
            {genres.map((g) => (
              <option key={g.genre} value={g.genre}>{g.genre} ({g.count})</option>
            ))}
          </select>

          <select
            value={sort}
            onChange={(e) => { setSort(e.target.value); setPage(1); }}
            className="bg-slate-800 border border-slate-700 rounded-xl px-3 py-2.5 text-white text-sm focus:ring-2 focus:ring-blue-500 outline-none"
          >
            <option value="-rating">Highest Rated</option>
            <option value="rating">Lowest Rated</option>
            <option value="title">A → Z</option>
            <option value="-title">Z → A</option>
            <option value="-created_at">Newest First</option>
          </select>
        </div>

        {/* Content */}
        {loading ? (
          <LoadingSpinner text="Loading books…" />
        ) : error ? (
          <ErrorMessage error={error} onRetry={fetchBooks} />
        ) : books.length === 0 ? (
          <div className="text-center py-20">
            <div className="text-6xl mb-4">📚</div>
            <p className="text-xl text-slate-300 mb-2">No books found</p>
            <p className="text-slate-500 text-sm mb-6">Try scraping books from the web to get started.</p>
            <button onClick={() => setShowScrapeModal(true)} className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-medium transition-colors">
              Scrape Books Now
            </button>
          </div>
        ) : (
          <>
            <p className="text-slate-500 text-sm mb-4">{totalCount} books found</p>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
              {books.map((book) => (
                <BookCard key={book.id} book={book} />
              ))}
            </div>

            {/* Pagination */}
            {totalCount > 20 && (
              <div className="flex justify-center gap-2 mt-8">
                <button
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 disabled:opacity-40 text-white rounded-lg text-sm transition-colors"
                >
                  Previous
                </button>
                <span className="px-4 py-2 text-slate-400 text-sm">Page {page} of {Math.ceil(totalCount / 20)}</span>
                <button
                  onClick={() => setPage(p => p + 1)}
                  disabled={page >= Math.ceil(totalCount / 20)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 disabled:opacity-40 text-white rounded-lg text-sm transition-colors"
                >
                  Next
                </button>
              </div>
            )}
          </>
        )}
      </div>

      {showScrapeModal && (
        <ScrapeModal
          onClose={() => setShowScrapeModal(false)}
          onSuccess={() => { fetchBooks(); api.getStats().then(setStats).catch(() => {}); }}
        />
      )}
    </div>
  );
}
