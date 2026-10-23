import { useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

export function LoginPage() {
  const [searchParams] = useSearchParams();
  const { handleCallback, login, isLoading } = useAuth();

  useEffect(() => {
    const code = searchParams.get('code');
    const state = searchParams.get('state');

    if (code && state) {
      const codeVerifier = sessionStorage.getItem('code_verifier');
      if (codeVerifier) {
        handleCallback(code, state, codeVerifier).catch((err) => {
          console.error('Auth callback failed:', err);
          alert('Authentication failed. Please try again.');
          window.location.href = '/';
        });
      }
    }
  }, [searchParams, handleCallback]);

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
      <div className="container max-w-md mx-auto my-xl">
        <div className="card">
          <div className="card-header text-center">
            <h1 className="font-semibold text-lg">Welcome to Beacon Hub</h1>
            <p className="text-sm text-muted mt-sm">Open-source Grok Bot alternative</p>
          </div>
          <div className="card-body">
            <div className="text-center mb-lg">
              <p className="text-muted mb-md">
                Sign in with your Keycloak account to access Beacon Hub.
              </p>
              <button className="btn btn-primary btn-lg w-full" onClick={login} disabled={isLoading}>
                {isLoading ? 'Loading...' : 'Sign In with Keycloak'}
              </button>
            </div>
            <div className="border-t pt-md text-center">
              <p className="text-xs text-muted">
                By signing in, you agree to our Terms of Service and Privacy Policy.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}