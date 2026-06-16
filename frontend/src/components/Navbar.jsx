import { Link, useLocation } from 'react-router-dom';
import { BookOpenIcon, MagnifyingGlassIcon, HomeIcon, ChatBubbleLeftRightIcon } from '@heroicons/react/24/outline';

export default function Navbar() {
  const { pathname } = useLocation();
  const links = [
    { to: '/', label: 'Library', icon: HomeIcon },
    { to: '/ask', label: 'Ask AI', icon: ChatBubbleLeftRightIcon },
  ];
  return (
    <nav className="bg-slate-900 border-b border-slate-700 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <Link to="/" className="flex items-center gap-2 text-blue-400 font-bold text-xl">
            <BookOpenIcon className="h-7 w-7" />
            <span>BookIQ</span>
            <span className="text-xs bg-blue-600 text-white px-2 py-0.5 rounded-full font-normal">AI</span>
          </Link>
          <div className="flex items-center gap-1">
            {links.map(({ to, label, icon: Icon }) => (
              <Link
                key={to}
                to={to}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors
                  ${pathname === to
                    ? 'bg-blue-600 text-white'
                    : 'text-slate-300 hover:bg-slate-800 hover:text-white'}`}
              >
                <Icon className="h-4 w-4" />
                {label}
              </Link>
            ))}
          </div>
        </div>
      </div>
    </nav>
  );
}
