import { useState, useEffect } from 'react';
import { api } from '../api/client';
import type { HealthResponse } from '../types/api';

export function Health() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadHealth();
  }, []);

  async function loadHealth() {
    try {
      setLoading(true);
      const data = await api.health();
      setHealth(data);
    } catch (err) {
      setError('Failed to load health status');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64" data-testid="health-spinner">
        <div className="spinner" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="container">
        <div className="alert alert-danger">{error}</div>
      </div>
    );
  }

  if (!health) return null;

  const statusColors = {
    healthy: 'badge-success',
    degraded: 'badge-warning',
  } as const;

  const statusClass = statusColors[health.status as keyof typeof statusColors] || 'badge-secondary';

  return (
    <div className="container">
      <div className="card">
        <div className="card-header">
          <h1 className="font-semibold text-lg">Health Status</h1>
        </div>
        <div className="card-body">
          <div className="flex items-center gap-md mb-lg">
            <span className={`badge ${statusClass}`}>{health.status}</span>
            <span className="text-sm text-muted">v{health.version} · {health.environment}</span>
          </div>
          <div className="grid gap-md" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))' }}>
            <div className="p-md bg-[var(--color-bg)] rounded-md">
              <div className="text-sm text-muted">Database</div>
              <div className={`font-medium ${health.database === 'connected' ? 'text-success' : 'text-danger'}`}>
                {health.database}
              </div>
            </div>
            <div className="p-md bg-[var(--color-bg)] rounded-md">
              <div className="text-sm text-muted">Version</div>
              <div className="font-medium">{health.version}</div>
            </div>
            <div className="p-md bg-[var(--color-bg)] rounded-md">
              <div className="text-sm text-muted">Environment</div>
              <div className="font-medium">{health.environment}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}