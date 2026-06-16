/**
 * BookIQ API Client
 * All backend communication goes through this module.
 */

const BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

async function request(path, options = {}) {
  const url = `${BASE_URL}${path}`;
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: res.statusText }));
    throw new Error(err.error || `HTTP ${res.status}`);
  }
  return res.json();
}

export const api = {
  // Books
  getBooks: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return request(`/books/${qs ? '?' + qs : ''}`);
  },
  getBook: (id) => request(`/books/${id}/`),
  getRecommendations: (id) => request(`/books/${id}/recommendations/`),
  uploadBook: (data) => request('/books/upload/', { method: 'POST', body: JSON.stringify(data) }),

  // AI
  askQuestion: (question) =>
    request('/ask/', { method: 'POST', body: JSON.stringify({ question }) }),

  // Scraper
  scrapeBooks: (data) =>
    request('/scrape/', { method: 'POST', body: JSON.stringify(data) }),

  // Utility
  getGenres: () => request('/genres/'),
  getStats: () => request('/stats/'),
  getChatHistory: () => request('/chat-history/'),
};
