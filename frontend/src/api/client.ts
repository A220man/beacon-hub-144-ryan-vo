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

class ApiClient { … }

export const api = new ApiClient();

// Health
async healthCheck(): Promise<HealthResponse> {
  const response = await this.client.get<HealthResponse>('/health');
  return response.data;
}

// Agents
async listAgents(page: number = 1, pageSize: number = 20): Promise<PaginatedResponse> {
  const response = await this.client.get<PaginatedResponse>('/agents', {
    params: { page, page_size: pageSize },
  });
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

async updateAgent(id: number, agentData: Partial<AgentCreate>): Promise<Agent> {
  const response = await this.client.patch<Agent>(`/agents/${id}`, agentData);
  return response.data;
}

async deleteAgent(id: number): Promise<void> {
  await this.client.delete(`/agents/${id}`);
  return;
}

// Models
async listModels(providerId: number, page: number = 1, pageSize: number = 20): Promise<PaginatedResponse> {
  const response = await this.client.get<PaginatedResponse>(`/providers/${providerId}/models`, {
    params: { page, page_size: pageSize },
  });
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

async sendMessage(
  conversationId: number,
  role: "user" | "assistant" | "system" | "tool",
  content: string,
  toolCalls?: any[],
  toolCallId?: string,
): Promise<Message> {
  const response = await this.client.post<Message>(
    `/conversations/${conversationId}/messages`,
    { role, content, toolCalls, toolCallId }
  );
  return response.data;
}
