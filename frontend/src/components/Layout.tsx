import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { ReactNode } from 'react';

interface LayoutProps {
  children?: ReactNode;
}

export function Layout({ children }: LayoutProps) {
  const { user, isAuthenticated, logout, isLoading } = useAuth();
  const location = useLocation();

  const navigation = [
    { path: '/', label: 'Health' },
    { path: '/providers', label: 'Providers' },
    { path: '/agents', label: 'Agents' },
    { path: '/chat', label: 'Chat' },
    { path: '/tasks', label: 'Tasks' },
  ];

  if (isLoading) {
    return (
      <div className="page">
        <div className="flex items-center justify-center h-screen">
          <div className="spinner" />
        </div>
      </div>
    );
  }

  return (
    <div className="page">
      <header className="page-header">
        <div className="container flex justify-between items-center">
          <Link to="/" className="font-semibold text-lg text-primary">
            Beacon Hub
          </Link>
          <nav className="flex items-center gap-md">
            {isAuthenticated && (
              <>
                {navigation.map((item) => (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`text-sm ${location.pathname === item.path ? 'text-primary font-medium' : 'text-muted'}`}
                  >
                    {item.label}
                  </Link>
                ))}
                <div className="flex items-center gap-md">
                  <span className="text-sm text-muted">{user?.username}</span>
                  <button className="btn btn-outline btn-sm" onClick={logout}>
                    Logout
                  </button>
                </div>
              </>
            )}
            {!isAuthenticated && (
              <button className="btn btn-primary" onClick={() => {}}>
                Sign In
              </button>
            )}
          </nav>
        </div>
      </header>
      <main className="page-content">
        <div className="container">
          {children}
        </div>
      </main>
      <footer className="page-footer">
        <div className="container text-center">
          Beacon Hub &copy; 2026 Ryan Vo &mdash; Open-source Grok Bot alternative
        </div>
      </footer>
    </div>
  );
}