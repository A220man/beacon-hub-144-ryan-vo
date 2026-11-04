import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/Layout';
import { Health } from './components/Health';
import { Providers } from './components/Providers';
import { AuthProvider, useAuth } from './hooks/useAuth';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="spinner" />
      </div>
    );
  }
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />;
}

export function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Layout>
          <Routes>
            <Route path="/login" element={<div className="container py-xl text-center"><h2>Sign in with Keycloak</h2><p className="text-muted">OIDC login flow would redirect here</p></div>} />
            <Route path="/callback" element={<div className="container py-xl text-center"><h2>Processing login...</h2></div>} />
            <Route
              path="/*"
              element={
                <ProtectedRoute>
                  <Routes>
                    <Route path="/" element={<Health />} />
                    <Route path="/providers" element={<Providers />} />
                    <Route path="/agents" element={<div className="container py-xl text-center"><h2>Agents</h2><p className="text-muted">Coming soon</p></div>} />
                    <Route path="/chat" element={<div className="container py-xl text-center"><h2>Chat</h2><p className="text-muted">Coming soon</p></div>} />
                    <Route path="/tasks" element={<div className="container py-xl text-center"><h2>Tasks</h2><p className="text-muted">Coming soon</p></div>} />
                    <Route path="*" element={<Navigate to="/" replace />} />
                  </Routes>
                </ProtectedRoute>
              }
            />
          </Routes>
        </Layout>
      </BrowserRouter>
    </AuthProvider>
  );
}
