import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { api } from '../api/client';
import type { User } from '../types/api';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: () => Promise<void>;
  logout: () => Promise<void>;
  handleCallback: (code: string, state: string, codeVerifier: string) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    checkAuth();
  }, []);

  async function checkAuth() {
    try {
      const userData = await api.getMe();
      setUser(userData);
    } catch {
      // Not authenticated
    } finally {
      setIsLoading(false);
    }
  }

  async function login() {
    const { auth_url, state } = await api.getAuthUrl();
    // Generate PKCE code verifier
    const codeVerifier = generateCodeVerifier();

    // Store state and code verifier in sessionStorage
    sessionStorage.setItem('oidc_state', state);
    sessionStorage.setItem('code_verifier', codeVerifier);

    // Redirect to Keycloak
    window.location.href = auth_url;
  }

  async function handleCallback(code: string, state: string, codeVerifier: string) {
    const storedState = sessionStorage.getItem('oidc_state');
    const storedVerifier = sessionStorage.getItem('code_verifier');

    if (storedState !== state || storedVerifier !== codeVerifier) {
      throw new Error('Invalid state or code verifier');
    }

    const tokens = await api.exchangeCode(code, state, codeVerifier);
    api.setAccessToken(tokens.access_token);

    // Store refresh token in memory (not localStorage)
    sessionStorage.setItem('refresh_token', tokens.refresh_token || '');

    // Clear PKCE values
    sessionStorage.removeItem('oidc_state');
    sessionStorage.removeItem('code_verifier');

    // Fetch user info
    await checkAuth();
  }

  async function logout() {
    await api.logout();
    api.setAccessToken(null);
    sessionStorage.removeItem('refresh_token');
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, isAuthenticated: !!user, isLoading, login, logout, handleCallback }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

// PKCE utilities
function generateCodeVerifier(): string {
  const array = new Uint8Array(64);
  crypto.getRandomValues(array);
  return base64urlEncode(array);
}


function base64urlEncode(buffer: Uint8Array): string {
  return btoa(String.fromCharCode(...buffer))
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=/g, '');
}