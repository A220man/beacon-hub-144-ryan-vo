import { useState, useEffect, FormEvent, ChangeEvent } from 'react';
import { api } from '../api/client';
import type { Provider, ProviderCreate, Model, ModelCreate } from '../types/api';

type ProviderType = 'openai-compatible' | 'anthropic' | 'gemini' | 'ollama';
type ModelType = 'chat' | 'embedding' | 'image-generation' | 'video-generation';

export function Providers() {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [models, setModels] = useState<Record<number, Model[]>>({});
  const [loading, setLoading] = useState(true);
  const [showCreateProvider, setShowCreateProvider] = useState(false);
  const [showCreateModel, setShowCreateModel] = useState<number | null>(null);
  const [newProvider, setNewProvider] = useState<ProviderCreate>({
    name: '',
    provider_type: 'openai-compatible',
    base_url: '',
    api_key: '',
    config: {},
  });
  const [newModel, setNewModel] = useState<ModelCreate>({
    model_id: '',
    display_name: '',
    model_type: 'chat',
    context_window: 4096,
    supports_streaming: true,
    supports_tools: false,
    supports_vision: false,
    config: {},
  });
  const [selectedProviderId, setSelectedProviderId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadProviders();
  }, []);

  async function loadProviders() {
    try {
      setLoading(true);
      const response = await api.listProviders({ page_size: 50 });
      setProviders(response.items);
      // Load models for each provider
      for (const provider of response.items) {
        const modelsResponse = await api.listModels(provider.id, { page_size: 50 });
        setModels((prev) => ({ ...prev, [provider.id]: modelsResponse.items }));
      }
    } catch (err) {
      setError('Failed to load providers');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  async function handleCreateProvider(e: FormEvent) {
    e.preventDefault();
    try {
      setError(null);
      const provider = await api.createProvider(newProvider);
      setProviders((prev) => [provider, ...prev]);
      setShowCreateProvider(false);
      setNewProvider({ name: '', provider_type: 'openai-compatible', base_url: '', api_key: '', config: {} });
    } catch (err) {
      setError('Failed to create provider');
      console.error(err);
    }
  }

  async function handleCreateModel(e: FormEvent) {
    e.preventDefault();
    if (!selectedProviderId) return;
    try {
      setError(null);
      const model = await api.createModel(selectedProviderId, newModel);
      setModels((prev) => ({
        ...prev,
        [selectedProviderId]: [model, ...(prev[selectedProviderId] || [])],
      }));
      setShowCreateModel(null);
      setNewModel({ model_id: '', display_name: '', model_type: 'chat', context_window: 4096, supports_streaming: true, supports_tools: false, supports_vision: false, config: {} });
    } catch (err) {
      setError('Failed to create model');
      console.error(err);
    }
  }

  async function handleDeleteProvider(id: number) {
    if (!confirm('Delete this provider? This will also delete all associated models.')) return;
    try {
      await api.deleteProvider(id);
      setProviders((prev) => prev.filter((p) => p.id !== id));
      setModels((prev) => {
        const next = { ...prev };
        delete next[id];
        return next;
      });
    } catch (err) {
      setError('Failed to delete provider');
      console.error(err);
    }
  }

  async function handleDeleteModel(providerId: number, modelId: number) {
    if (!confirm('Delete this model?')) return;
    try {
      await api.deleteModel(providerId, modelId);
      setModels((prev) => ({
        ...prev,
        [providerId]: prev[providerId].filter((m) => m.id !== modelId),
      }));
    } catch (err) {
      setError('Failed to delete model');
      console.error(err);
    }
  }

  function handleProviderTypeChange(e: ChangeEvent<HTMLSelectElement>) {
    setNewProvider({ ...newProvider, provider_type: e.target.value as ProviderType });
  }

  function handleModelTypeChange(e: ChangeEvent<HTMLSelectElement>) {
    setNewModel({ ...newModel, model_type: e.target.value as ModelType });
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="spinner" />
      </div>
    );
  }

  return (
    <div className="container">
      <div className="flex justify-between items-center mb-lg">
        <h1 className="font-semibold text-lg">Providers & Models</h1>
        <button className="btn btn-primary" onClick={() => setShowCreateProvider(true)}>
          Add Provider
        </button>
      </div>

      {error && <div className="alert alert-danger mb-md">{error}</div>}

      {showCreateProvider && (
        <div className="card mb-lg">
          <div className="card-header">
            <h2 className="font-medium">Add Provider</h2>
          </div>
          <div className="card-body">
            <form onSubmit={handleCreateProvider} className="flex flex-col gap-md max-w-md">
              <div className="form-group">
                <label className="form-label">Name</label>
                <input
                  type="text"
                  className="form-input"
                  value={newProvider.name}
                  onChange={(e) => setNewProvider({ ...newProvider, name: e.target.value })}
                  required
                  placeholder="My OpenAI"
                />
              </div>
              <div className="form-group">
                <label className="form-label">Provider Type</label>
                <select
                  className="form-input"
                  value={newProvider.provider_type}
                  onChange={handleProviderTypeChange}
                  required
                >
                  <option value="openai-compatible">OpenAI Compatible</option>
                  <option value="anthropic">Anthropic</option>
                  <option value="gemini">Gemini</option>
                  <option value="ollama">Ollama</option>
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Base URL (optional)</label>
                <input
                  type="url"
                  className="form-input"
                  value={newProvider.base_url}
                  onChange={(e) => setNewProvider({ ...newProvider, base_url: e.target.value })}
                  placeholder="https://api.openai.com/v1"
                />
              </div>
              <div className="form-group">
                <label className="form-label">API Key</label>
                <input
                  type="password"
                  className="form-input"
                  value={newProvider.api_key}
                  onChange={(e) => setNewProvider({ ...newProvider, api_key: e.target.value })}
                  required
                  placeholder="sk-..."
                />
              </div>
              <div className="flex justify-end gap-sm">
                <button type="button" className="btn btn-outline" onClick={() => setShowCreateProvider(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Create Provider
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {providers.length === 0 && !showCreateProvider && (
        <div className="card text-center py-xl">
          <p className="text-muted mb-md">No providers configured yet</p>
          <button className="btn btn-primary" onClick={() => setShowCreateProvider(true)}>
            Add Your First Provider
          </button>
        </div>
      )}

      <div className="space-y-md">
        {providers.map((provider) => (
          <div key={provider.id} className="card">
            <div className="card-header flex justify-between items-center">
              <div className="flex items-center gap-md">
                <span className={`badge ${provider.is_active ? 'badge-success' : 'badge-secondary'}`}>
                  {provider.provider_type}
                </span>
                <h3 className="font-medium">{provider.name}</h3>
                {provider.base_url && (
                  <span className="text-sm text-muted">{provider.base_url}</span>
                )}
              </div>
              <div className="flex gap-sm">
                <button
                  className="btn btn-outline btn-sm"
                  onClick={() => {
                    setSelectedProviderId(provider.id);
                    setShowCreateModel(provider.id);
                  }}
                >
                  Add Model
                </button>
                <button
                  className="btn btn-outline btn-sm btn-danger"
                  onClick={() => handleDeleteProvider(provider.id)}
                >
                  Delete
                </button>
              </div>
            </div>
            <div className="card-body">
              {showCreateModel === provider.id && (
                <form onSubmit={handleCreateModel} className="flex flex-col gap-md max-w-md mb-md p-md bg-[var(--color-bg)] rounded-md">
                  <h4 className="font-medium">Add Model</h4>
                  <div className="form-group">
                    <label className="form-label">Model ID</label>
                    <input
                      type="text"
                      className="form-input"
                      value={newModel.model_id}
                      onChange={(e) => setNewModel({ ...newModel, model_id: e.target.value })}
                      required
                      placeholder="gpt-4o-mini"
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Display Name</label>
                    <input
                      type="text"
                      className="form-input"
                      value={newModel.display_name}
                      onChange={(e) => setNewModel({ ...newModel, display_name: e.target.value })}
                      required
                      placeholder="GPT-4o Mini"
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Model Type</label>
                    <select
                      className="form-input"
                      value={newModel.model_type}
                      onChange={handleModelTypeChange}
                    >
                      <option value="chat">Chat</option>
                      <option value="embedding">Embedding</option>
                      <option value="image-generation">Image Generation</option>
                      <option value="video-generation">Video Generation</option>
                    </select>
                  </div>
                  <div className="flex justify-end gap-sm">
                    <button type="button" className="btn btn-outline btn-sm" onClick={() => setShowCreateModel(null)}>
                      Cancel
                    </button>
                    <button type="submit" className="btn btn-primary btn-sm">
                      Add Model
                    </button>
                  </div>
                </form>
              )}

              <div className="space-y-sm">
                {(models[provider.id] || []).map((model) => (
                  <div key={model.id} className="flex justify-between items-center p-sm bg-[var(--color-bg)] rounded-md">
                    <div className="flex items-center gap-md">
                      <span className={`badge ${model.is_active ? 'badge-success' : 'badge-secondary'}`}>
                        {model.model_type}
                      </span>
                      <div>
                        <div className="font-medium">{model.display_name}</div>
                        <div className="text-sm text-muted">{model.model_id}</div>
                      </div>
                      <div className="flex items-center gap-sm text-xs text-muted">
                        {model.supports_streaming && <span className="badge badge-primary">Streaming</span>}
                        {model.supports_tools && <span className="badge badge-primary">Tools</span>}
                        {model.supports_vision && <span className="badge badge-primary">Vision</span>}
                        <span>Ctx: {model.context_window.toLocaleString()}</span>
                      </div>
                    </div>
                    <button
                      className="btn btn-outline btn-sm btn-danger"
                      onClick={() => handleDeleteModel(provider.id, model.id)}
                    >
                      Delete
                    </button>
                  </div>
                ))}
                {(models[provider.id] || []).length === 0 && (
                  <p className="text-sm text-muted text-center py-md">No models registered yet</p>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}