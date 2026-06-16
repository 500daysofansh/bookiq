import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import BookDetail from './pages/BookDetail';
import AskAI from './pages/AskAI';

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-slate-950 text-white">
        <Navbar />
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/books/:id" element={<BookDetail />} />
          <Route path="/ask" element={<AskAI />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}
