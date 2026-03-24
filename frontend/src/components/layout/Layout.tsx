import { useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { useTheme } from '../../context/ThemeContext';
import { useWebSocket } from '../../hooks/useWebSocket';
import { useDashboard } from '../../hooks/useDashboard';
import LiveIndicator from '../status/LiveIndicator';

const navItems = [
  { path: '/dashboard', label: 'Dashboard', shortcut: 'd' },
  { path: '/hosts', label: 'Hosts', shortcut: 'h' },
  { path: '/alerts', label: 'Alerts', shortcut: 'a' },
];

// Map child routes to their logical parent for the back button
function getParentRoute(pathname: string): string | null {
  if (pathname === '/dashboard' || pathname === '/') return null;
  // /hosts/123 → /hosts
  if (/^\/hosts\/\d+/.test(pathname)) return '/hosts';
  // /hosts?status=xxx → /dashboard
  if (pathname === '/hosts') return '/dashboard';
  // /alerts → /dashboard
  if (pathname === '/alerts') return '/dashboard';
  return '/dashboard';
}

function getBackLabel(pathname: string): string {
  if (/^\/hosts\/\d+/.test(pathname)) return 'Back to Hosts';
  if (pathname === '/hosts' || pathname === '/alerts') return 'Back to Dashboard';
  return 'Back';
}

function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();
  return (
    <button
      onClick={toggleTheme}
      className="p-2 rounded-lg text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
      title={theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
    >
      {theme === 'dark' ? (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
        </svg>
      ) : (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
        </svg>
      )}
    </button>
  );
}

export default function Layout({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const parentRoute = getParentRoute(location.pathname);
  const backLabel = getBackLabel(location.pathname);
  const { connected } = useWebSocket([]);
  const { data: summary } = useDashboard();
  const alertCount = summary?.active_alerts ?? 0;

  // Keyboard shortcuts: d=dashboard, h=hosts, a=alerts
  useEffect(() => {
    function handleKey(e: KeyboardEvent) {
      // Ignore when user is typing in an input/textarea
      const tag = (e.target as HTMLElement)?.tagName;
      if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;
      if (e.ctrlKey || e.metaKey || e.altKey) return;

      switch (e.key.toLowerCase()) {
        case 'd': navigate('/dashboard'); break;
        case 'h': navigate('/hosts'); break;
        case 'a': navigate('/alerts'); break;
      }
    }
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [navigate]);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <Link to="/dashboard" className="flex items-center space-x-2">
              <span className="text-xl font-bold text-indigo-600 dark:text-indigo-400">RecSignal</span>
              <span className="text-sm text-gray-400 dark:text-gray-500">Server Monitor</span>
              <LiveIndicator connected={connected} />
            </Link>
            <nav className="flex items-center space-x-1">
              {navItems.map((item) => (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`relative px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                    location.pathname.startsWith(item.path)
                      ? 'bg-indigo-50 text-indigo-700 dark:bg-indigo-900/50 dark:text-indigo-300'
                      : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900 dark:text-gray-300 dark:hover:bg-gray-700 dark:hover:text-white'
                  }`}
                  title={`${item.label} (${item.shortcut})`}
                >
                  {item.label}
                  {item.path === '/alerts' && alertCount > 0 && (
                    <span className="absolute -top-1 -right-1 inline-flex items-center justify-center w-5 h-5 text-xs font-bold text-white bg-red-500 rounded-full">
                      {alertCount > 99 ? '99+' : alertCount}
                    </span>
                  )}
                </Link>
              ))}

              <ThemeToggle />

              {/* User menu */}
              {user && (
                <div className="flex items-center ml-4 pl-4 border-l border-gray-200 dark:border-gray-600">
                  <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 rounded-full bg-indigo-100 dark:bg-indigo-900 flex items-center justify-center">
                      <span className="text-sm font-semibold text-indigo-700 dark:text-indigo-300">
                        {user.display_name.charAt(0).toUpperCase()}
                      </span>
                    </div>
                    <div className="hidden sm:block">
                      <p className="text-sm font-medium text-gray-700 dark:text-gray-200 leading-none">{user.display_name}</p>
                      <p className="text-xs text-gray-400 dark:text-gray-500 mt-0.5">{user.role}</p>
                    </div>
                    <button
                      onClick={logout}
                      className="ml-2 px-3 py-1.5 text-xs font-medium text-gray-500 hover:text-red-600 hover:bg-red-50 dark:text-gray-400 dark:hover:text-red-400 dark:hover:bg-red-900/30 rounded-md transition-colors"
                    >
                      Sign Out
                    </button>
                  </div>
                </div>
              )}
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {parentRoute && (
          <button
            onClick={() => navigate(parentRoute)}
            className="mb-4 inline-flex items-center gap-1.5 text-sm text-gray-500 hover:text-indigo-600 dark:text-gray-400 dark:hover:text-indigo-400 transition-colors"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
            </svg>
            {backLabel}
          </button>
        )}
        {children}
      </main>
    </div>
  );
}
