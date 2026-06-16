import { Link } from 'react-router-dom';
import { StarIcon } from '@heroicons/react/24/solid';

function Stars({ rating }) {
  return (
    <div className="flex items-center gap-0.5">
      {[1, 2, 3, 4, 5].map((s) => (
        <StarIcon
          key={s}
          className={`h-3.5 w-3.5 ${s <= Math.round(rating) ? 'text-yellow-400' : 'text-slate-600'}`}
        />
      ))}
      <span className="text-xs text-slate-400 ml-1">{rating?.toFixed(1)}</span>
    </div>
  );
}

export default function BookCard({ book }) {
  const FALLBACK = `https://via.placeholder.com/128x192/1e293b/3b82f6?text=${encodeURIComponent(book.title?.slice(0, 10))}`;

  return (
    <Link to={`/books/${book.id}`} className="group block">
      <div className="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden hover:border-blue-500 hover:shadow-lg hover:shadow-blue-900/30 transition-all duration-200 h-full flex flex-col">
        {/* Cover */}
        <div className="relative overflow-hidden bg-slate-700 aspect-[2/3]">
          <img
            src={book.cover_image_url || FALLBACK}
            alt={book.title}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
            onError={(e) => { e.target.src = FALLBACK; }}
          />
          {book.genre && (
            <span className="absolute top-2 left-2 bg-blue-600/90 text-white text-xs px-2 py-0.5 rounded-full backdrop-blur-sm">
              {book.genre}
            </span>
          )}
        </div>

        {/* Info */}
        <div className="p-3 flex flex-col gap-1 flex-1">
          <h3 className="text-sm font-semibold text-white line-clamp-2 leading-tight group-hover:text-blue-400 transition-colors">
            {book.title}
          </h3>
          <p className="text-xs text-slate-400">{book.author || 'Unknown Author'}</p>
          {book.rating != null && <Stars rating={book.rating} />}
          {book.price && (
            <p className="text-sm font-bold text-green-400 mt-auto pt-1">{book.price}</p>
          )}
        </div>
      </div>
    </Link>
  );
}
