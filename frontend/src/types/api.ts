export interface HealthResponse {
  status: string;
  version: string;
  environment: string;
  database: string;
}

export interface Provider {
  id: number;
  name: string;
  provider_type: string;
  base_url: string | null;
  is_active: boolean;
  config: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  owner_id: number;
}

export interface ProviderCreate {
  name: string;
  provider_type: 'openai-compatible' | 'anthropic' | 'gemini' | 'ollama';
  base_url?: string;
  api_key: string;
  config?: Record<string, unknown>;
}

export interface ProviderUpdate {
  name?: string;
  base_url?: string;
  api_key?: string;
  config?: Record<string, unknown>;
  is_active?: boolean;
}

export interface Model {
  id: number;
  provider_id: number;
  model_id: string;
  display_name: string;
  model_type: 'chat' | 'embedding' | 'image-generation' | 'video-generation';
  context_window: number;
  max_output_tokens: number | null;
  supports_streaming: boolean;
  supports_tools: boolean;
  supports_vision: boolean;
  is_active: boolean;
  config: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface ModelCreate {
  model_id: string;
  display_name: string;
  model_type?: 'chat' | 'embedding' | 'image-generation' | 'video-generation';
  context_window?: number;
  max_output_tokens?: number;
  supports_streaming?: boolean;
  supports_tools?: boolean;
  supports_vision?: boolean;
  config?: Record<string, unknown>;
}

export interface ModelUpdate {
  display_name?: string;
  model_type?: 'chat' | 'embedding' | 'image-generation' | 'video-generation';
  context_window?: number;
  max_output_tokens?: number;
  supports_streaming?: boolean;
  supports_tools?: boolean;
  supports_vision?: boolean;
  config?: Record<string, unknown>;
  is_active?: boolean;
}

export interface Agent {
  id: number;
  owner_id: number;
  model_id: number;
  name: string;
  description: string | null;
  system_prompt: string | null;
  temperature: number;
  max_tokens: number | null;
  tools: string[];
  is_active: boolean;
  config: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface AgentCreate {
  model_id: number;
  name: string;
  description?: string;
  system_prompt?: string;
  temperature?: number;
  max_tokens?: number;
  tools?: string[];
  config?: Record<string, unknown>;
}

export interface Conversation {
  id: number;
  owner_id: number;
  agent_id: number;
  title: string;
  is_active: boolean;
  meta: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface ConversationCreate {
  agent_id: number;
  title: string;
}

export interface Message {
  id: number;
  conversation_id: number;
  role: 'user' | 'assistant' | 'system' | 'tool';
  content: string | null;
  tool_calls: unknown[] | null;
  tool_call_id: string | null;
  meta: Record<string, unknown>;
  created_at: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface User {
  id: number;
  oidc_sub: string;
  username: string;
  email: string | null;
  full_name: string | null;
  is_active: boolean;
  is_admin: boolean;
  roles: string[];
  created_at: string;
}

export interface AuthUrlResponse {
  auth_url: string;
  state: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  refresh_token?: string;
  id_token?: string;
}