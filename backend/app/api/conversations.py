"""Conversation and message management API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import get_settings
from app.core.database import get_db
from app.models import Conversation, Message, Agent, Provider, User
from app.schemas import (
    ConversationBase,
    ConversationCreate,
    ConversationUpdate,
    ConversationResponse,
    MessageBase,
    MessageCreate,
    MessageResponse,
    PaginatedResponse,
)
from app.core.security import get_current_user_id

router = APIRouter(prefix="/conversations", tags=["conversations"])
settings = get_settings()


async def get_user_conversations(user_id: int, db: AsyncSession):
    """Get conversations owned by user."""
    query = select(Conversation).where(Conversation.owner_id == user_id)
    query = query.order_by(Conversation.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.get("", response_model=PaginatedResponse)
async def list_conversations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_active: bool | None = Query(None),
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> PaginatedResponse:
    """List conversations for current user with pagination."""
    query = select(Conversation).where(Conversation.owner_id == user_id)
    if is_active is not None:
        query = query.where(Conversation.is_active == is_active)
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    conversations = result.scalars().all()
    return PaginatedResponse(
        items=[ConversationResponse.model_validate(c) for c in conversations],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> ConversationResponse:
    """Get a specific conversation."""
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id, Conversation.owner_id == user_id
        )
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return ConversationResponse.model_validate(conversation)


@router.post("/{conversation_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def create_message(
    conversation_id: int,
    message_data: MessageCreate,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> MessageResponse:
    """Create a message in a conversation."""
    # Verify conversation exists and user owns it
    conv_result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id, Conversation.owner_id == user_id
        )
    )
    conversation = conv_result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Verify model belongs to user if provided
    if message_data.model_id is not None:
        from app.models import Model
        model_result = await db.execute(
            select(Model).join(Provider).where(Model.id == message_data.model_id, Provider.owner_id == user_id)
        )
        model = model_result.scalar_one_or_none()
        if not model:
            raise HTTPException(status_code=404, detail="Model not found or not owned by user")

    # Create the message
    message = Message(
        role=message_data.role,
        content=message_data.content,
        tool_calls=message_data.tool_calls,
        tool_call_id=message_data.tool_call_id,
        meta=message_data.meta or {},
        conversation_id=conversation_id,
        model_id=message_data.model_id,
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return MessageResponse.model_validate(message)


@router.get("/{conversation_id}/messages", response_model=list[MessageResponse])
async def list_messages(
    conversation_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> list[MessageResponse]:
    """List all messages in a conversation."""
    # Verify conversation exists and user owns it
    conv_result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id, Conversation.owner_id == user_id
        )
    )
    conversation = conv_result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    query = select(Message).where(Message.conversation_id == conversation_id)
    query = query.order_by(Message.created_at.asc())
    result = await db.execute(query)
    messages = result.scalars().all()
    return [MessageResponse.model_validate(m) for m in messages]
