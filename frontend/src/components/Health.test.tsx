import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { Health } from './Health';
import { AuthProvider } from '../hooks/useAuth';

// Mock the API client
vi.mock('../api/client', () => ({
  api: {
    health: vi.fn(),
  },
}));

import { api } from '../api/client';

const mockHealthResponse = {
  status: 'healthy',
  version: '1.0.0',
  environment: 'test',
  database: 'connected',
};

describe('Health Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows loading spinner initially', () => {
    const { promise } = Promise.withResolvers();
    (api.health as vi.Mock).mockImplementation(() => promise);

    render(
      <BrowserRouter>
        <AuthProvider>
          <Health />
        </AuthProvider>
      </BrowserRouter>
    );

    // Check for spinner element
    expect(screen.getByTestId('health-spinner')).toBeInTheDocument();
  });

  it('displays health status when loaded', async () => {
    (api.health as vi.Mock).mockResolvedValue(mockHealthResponse);

    render(
      <BrowserRouter>
        <AuthProvider>
          <Health />
        </AuthProvider>
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Health Status')).toBeInTheDocument();
    });

    expect(screen.getByText('healthy')).toBeInTheDocument();
    expect(screen.getByText(/v1\.0\.0/)).toBeInTheDocument();
    expect(screen.getByText('test')).toBeInTheDocument();
    expect(screen.getByText('connected')).toBeInTheDocument();
  });

  it('shows error state when API fails', async () => {
    (api.health as vi.Mock).mockRejectedValue(new Error('Network error'));

    render(
      <BrowserRouter>
        <AuthProvider>
          <Health />
        </AuthProvider>
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Failed to load health status')).toBeInTheDocument();
    });
  });
});