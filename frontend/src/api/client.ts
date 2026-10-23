import axios, { AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import type {
  HealthResponse,
  Provider,
  ProviderCreate,
  ProviderUpdate,
  Model,
  ModelCreate,
  ModelUpdate,
  Agent,
  AgentCreate,
  Conversation,
  ConversationCreate,
  Message,
  PaginatedResponse,
  User,
  AuthUrlResponse,
  TokenResponse,
} from '../types/api';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

class ApiClient {
  private client: AxiosInstance;
  private accessToken: string | null = null;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
      withCredentials: true,
    });

    this.client.interceptors.request.use((config: InternalAxiosRequestConfig) => {
      if (this.accessToken) {
        config.headers.Authorization = `Bearer ${this.accessToken}`;
      }
      return config;
    });

    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          this.accessToken = null;
          // Could trigger logout here
        }
        return Promise.reject(error);
      }
    );
  }

  setAccessToken(token: string | null) {
    this.accessToken = token;
  }

  // Health
  async health(): Promise<HealthResponse> {
    const response = await this.client.get<HealthResponse>('/health');
    return response.data;
  }

  // Auth
  async getAuthUrl(): Promise<AuthUrlResponse> {
    const response = await this.client.get<AuthUrlResponse>('/auth/login');
    return response.data;
  }

  async exchangeCode(code: string, state: string, codeVerifier: string): Promise<TokenResponse> {
    const response = await this.client.post<TokenResponse>('/auth/callback', {
      code,
      state,
      code_verifier: codeVerifier,
    });
    return response.data;
  }

  async refreshToken(): Promise<TokenResponse> {
    const response = await this.client.post<TokenResponse>('/auth/refresh');
    return response.data;
  }

  async logout(): Promise<void> {
    await this.client.post('/auth/logout');
  }

  async getMe(): Promise<User> {
    const response = await this.client.get<User>('/auth/me');
    return response.data;
  }

  // Providers
  async listProviders(params?: { page?: number; page_size?: number; is_active?: boolean }): Promise<PaginatedResponse<Provider>> {
    const response = await this.client.get<PaginatedResponse<Provider>>('/providers', { params });
    return response.data;
  }

  async getProvider(id: number): Promise<Provider> {
    const response = await this.client.get<Provider>(`/providers/${id}`);
    return response.data;
  }

  async createProvider(data: ProviderCreate): Promise<Provider> {
    const response = await this.client.post<Provider>('/providers', data);
    return response.data;
  }

  async updateProvider(id: number, data: ProviderUpdate): Promise<Provider> {
    const response = await this.client.patch<Provider>(`/providers/${id}`, data);
    return response.data;
  }

  async deleteProvider(id: number): Promise<void> {
    await this.client.delete(`/providers/${id}`);
  }

  // Models
  async listModels(providerId: number, params?: { page?: number; page_size?: number; is_active?: boolean; model_type?: string }): Promise<PaginatedResponse<Model>> {
    const response = await this.client.get<PaginatedResponse<Model>>(`/providers/${providerId}/models`, { params });
    return response.data;
  }

  async getModel(providerId: number, modelId: number): Promise<Model> {
    const response = await this.client.get<Model>(`/providers/${providerId}/models/${modelId}`);
    return response.data;
  }

  async createModel(providerId: number, data: ModelCreate): Promise<Model> {
    const response = await this.client.post<Model>(`/providers/${providerId}/models`, data);
    return response.data;
  }

  async updateModel(providerId: number, modelId: number, data: ModelUpdate): Promise<Model> {
    const response = await this.client.patch<Model>(`/providers/${providerId}/models/${modelId}`, data);
    return response.data;
  }

  async deleteModel(providerId: number, modelId: number): Promise<void> {
    await this.client.delete(`/providers/${providerId}/models/${modelId}`);
  }

  // Agents
  async listAgents(): Promise<Agent[]> {
    const response = await this.client.get<Agent[]>('/agents');
    return response.data;
  }

  async getAgent(id: number): Promise<Agent> {
    const response = await this.client.get<Agent>(`/agents/${id}`);
    return response.data;
  }

  async createAgent(data: AgentCreate): Promise<Agent> {
    const response = await this.client.post<Agent>('/agents', data);
    return response.data;
  }

  // Conversations
  async listConversations(): Promise<Conversation[]> {
    const response = await this.client.get<Conversation[]>('/conversations');
    return response.data;
  }

  async getConversation(id: number): Promise<Conversation> {
    const response = await this.client.get<Conversation>(`/conversations/${id}`);
    return response.data;
  }

  async createConversation(data: ConversationCreate): Promise<Conversation> {
    const response = await this.client.post<Conversation>('/conversations', data);
    return response.data;
  }

  async getMessages(conversationId: number): Promise<Message[]> {
    const response = await this.client.get<Message[]>(`/conversations/${conversationId}/messages`);
    return response.data;
  }
}

export const api = new ApiClient();