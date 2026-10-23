"""Pydantic schemas for API request/response validation."""

from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field, EmailStr, HttpUrl, ConfigDict
from enum import Enum


class ProviderType(str, Enum):
    OPENAI_COMPATIBLE = "openai-compatible"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    OLLAMA = "ollama"


class ModelType(str, Enum):
    CHAT = "chat"
    EMBEDDING = "embedding"
    IMAGE_GENERATION = "image-generation"
    VIDEO_GENERATION = "video-generation"


# Provider schemas
class ProviderBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    provider_type: ProviderType
    base_url: Optional[HttpUrl] = None
    config: dict = Field(default_factory=dict)


class ProviderCreate(ProviderBase):
    api_key: str = Field(..., min_length=1)


class ProviderUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    base_url: Optional[HttpUrl] = None
    api_key: Optional[str] = None
    config: Optional[dict] = None
    is_active: Optional[bool] = None


class ProviderResponse(ProviderBase):
    id: int
    owner_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Model schemas
class ModelBase(BaseModel):
    model_id: str = Field(..., min_length=1, max_length=200)
    display_name: str = Field(..., min_length=1, max_length=200)
    model_type: ModelType = ModelType.CHAT
    context_window: int = Field(default=4096, ge=1)
    max_output_tokens: Optional[int] = Field(None, ge=1)
    supports_streaming: bool = True
    supports_tools: bool = False
    supports_vision: bool = False
    config: dict = Field(default_factory=dict)

    model_config = ConfigDict(protected_namespaces=())

class ModelCreate(ModelBase):
    pass


class ModelUpdate(BaseModel):
    display_name: Optional[str] = Field(None, min_length=1, max_length=200)
    model_type: Optional[ModelType] = None
    context_window: Optional[int] = Field(None, ge=1)
    max_output_tokens: Optional[int] = Field(None, ge=1)
    supports_streaming: Optional[bool] = None
    supports_tools: Optional[bool] = None
    supports_vision: Optional[bool] = None
    config: Optional[dict] = None
    is_active: Optional[bool] = None

    model_config = ConfigDict(protected_namespaces=())

class ModelResponse(ModelBase):
    id: int
    provider_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, protected_namespaces=())
# Agent schemas
class AgentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, ge=1)
    tools: list[str] = Field(default_factory=list)
    config: dict = Field(default_factory=dict)

    model_config = ConfigDict(protected_namespaces=())

class AgentCreate(AgentBase):
    model_id: int

    model_config = ConfigDict(protected_namespaces=())


class AgentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, ge=1)
    tools: Optional[list[str]] = None
    config: Optional[dict] = None
    is_active: Optional[bool] = None

    model_config = ConfigDict(protected_namespaces=())

class AgentResponse(AgentBase):
    id: int
    owner_id: int
    model_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

# Conversation schemas
class ConversationBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)


class ConversationCreate(ConversationBase):
    agent_id: int


class ConversationUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    is_active: Optional[bool] = None


class ConversationResponse(ConversationBase):
    id: int
    owner_id: int
    agent_id: int
    is_active: bool
    meta: dict
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Message schemas
class MessageBase(BaseModel):
    role: str = Field(..., pattern="^(user|assistant|system|tool)$")
    content: Optional[str] = None
    tool_calls: Optional[list[dict]] = None
    tool_call_id: Optional[str] = None
    meta: dict = Field(default_factory=dict)


class MessageCreate(MessageBase):
    conversation_id: int


class MessageResponse(MessageBase):
    id: int
    conversation_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Task schemas
class TaskBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    prompt: str = Field(..., min_length=1)
    schedule: Optional[str] = None
    config: dict = Field(default_factory=dict)

    model_config = ConfigDict(protected_namespaces=())

class TaskCreate(TaskBase):
    agent_id: int
    model_id: Optional[int] = None

    model_config = ConfigDict(protected_namespaces=())

class TaskUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    prompt: Optional[str] = None
    schedule: Optional[str] = None
    config: Optional[dict] = None
    is_active: Optional[bool] = None

    model_config = ConfigDict(protected_namespaces=())

class TaskResponse(TaskBase):
    id: int
    owner_id: int
    agent_id: int
    model_id: Optional[int]
    is_scheduled: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_run: Optional[datetime]
    next_run: Optional[datetime]

    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

# Task Run schemas
class TaskRunResponse(BaseModel):
    id: int
    task_id: int
    status: str
    input_data: dict
    output_data: Optional[dict]
    error: Optional[str]
    started_at: datetime
    completed_at: Optional[datetime]
    duration_ms: Optional[int]

    class Config:
        from_attributes = True


# Health check
class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
    database: str


# OIDC Auth schemas
class AuthUrlResponse(BaseModel):
    auth_url: str
    state: str


class TokenRequest(BaseModel):
    code: str
    state: str
    code_verifier: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: Optional[str] = None
    id_token: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    oidc_sub: str
    username: str
    email: Optional[str]
    full_name: Optional[str]
    is_active: bool
    is_admin: bool
    roles: list[str]
    created_at: datetime

    class Config:
        from_attributes = True


# Pagination
class PaginatedResponse(BaseModel):
    items: list[Any]
    total: int
    page: int
    page_size: int
    total_pages: int