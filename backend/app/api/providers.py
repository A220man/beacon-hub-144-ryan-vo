"""Provider and Model management API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import get_password_hash
from app.models import Provider, Model, User
from app.schemas import (
    ProviderCreate,
    ProviderUpdate,
    ProviderResponse,
    ModelCreate,
    ModelUpdate,
    ModelResponse,
    PaginatedResponse,
)

router = APIRouter(prefix="/providers", tags=["providers"])
settings = get_settings()


# Dependency to get current user (placeholder - in real app, use auth dependency)
async def get_current_user_id(request: Request) -> int:
    """Extract user ID from JWT cookie. Placeholder for actual auth dependency."""
    # This will be replaced with proper auth dependency
    return 1


# Provider endpoints
@router.post("", response_model=ProviderResponse, status_code=status.HTTP_201_CREATED)
async def create_provider(
    provider_data: ProviderCreate,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> ProviderResponse:
    """Create a new LLM provider connection."""
    provider = Provider(
        owner_id=user_id,
        name=provider_data.name,
        provider_type=provider_data.provider_type.value,
        base_url=str(provider_data.base_url) if provider_data.base_url else None,
        api_key_encrypted=get_password_hash(provider_data.api_key),  # Encrypt in real impl
        config=provider_data.config,
    )
    db.add(provider)
    await db.commit()
    await db.refresh(provider)
    return ProviderResponse.model_validate(provider)


@router.get("", response_model=PaginatedResponse)
async def list_providers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_active: bool | None = Query(None),
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> PaginatedResponse:
    """List providers for current user with pagination."""
    query = select(Provider).where(Provider.owner_id == user_id)
    if is_active is not None:
        query = query.where(Provider.is_active == is_active)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)

    # Paginate
    query = query.order_by(Provider.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    providers = result.scalars().all()

    return PaginatedResponse(
        items=[ProviderResponse.model_validate(p) for p in providers],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/{provider_id}", response_model=ProviderResponse)
async def get_provider(
    provider_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> ProviderResponse:
    """Get a specific provider."""
    result = await db.execute(
        select(Provider).where(Provider.id == provider_id, Provider.owner_id == user_id)
    )
    provider = result.scalar_one_or_none()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    return ProviderResponse.model_validate(provider)


@router.patch("/{provider_id}", response_model=ProviderResponse)
async def update_provider(
    provider_id: int,
    provider_data: ProviderUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> ProviderResponse:
    """Update a provider."""
    result = await db.execute(
        select(Provider).where(Provider.id == provider_id, Provider.owner_id == user_id)
    )
    provider = result.scalar_one_or_none()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    update_data = provider_data.model_dump(exclude_unset=True)
    if "api_key" in update_data:
        update_data["api_key_encrypted"] = get_password_hash(update_data.pop("api_key"))

    for field, value in update_data.items():
        setattr(provider, field, value)

    await db.commit()
    await db.refresh(provider)
    return ProviderResponse.model_validate(provider)


@router.delete("/{provider_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_provider(
    provider_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> None:
    """Delete a provider."""
    result = await db.execute(
        select(Provider).where(Provider.id == provider_id, Provider.owner_id == user_id)
    )
    provider = result.scalar_one_or_none()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    await db.delete(provider)
    await db.commit()


# Model endpoints
@router.post("/{provider_id}/models", response_model=ModelResponse, status_code=status.HTTP_201_CREATED)
async def create_model(
    provider_id: int,
    model_data: ModelCreate,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> ModelResponse:
    """Register a model under a provider."""
    # Verify provider ownership
    result = await db.execute(
        select(Provider).where(Provider.id == provider_id, Provider.owner_id == user_id)
    )
    provider = result.scalar_one_or_none()
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    model = Model(
        provider_id=provider_id,
        model_id=model_data.model_id,
        display_name=model_data.display_name,
        model_type=model_data.model_type.value,
        context_window=model_data.context_window,
        max_output_tokens=model_data.max_output_tokens,
        supports_streaming=model_data.supports_streaming,
        supports_tools=model_data.supports_tools,
        supports_vision=model_data.supports_vision,
        config=model_data.config,
    )
    db.add(model)
    await db.commit()
    await db.refresh(model)
    return ModelResponse.model_validate(model)


@router.get("/{provider_id}/models", response_model=PaginatedResponse)
async def list_models(
    provider_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_active: bool | None = Query(None),
    model_type: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> PaginatedResponse:
    """List models for a provider."""
    # Verify provider ownership
    result = await db.execute(
        select(Provider).where(Provider.id == provider_id, Provider.owner_id == user_id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Provider not found")

    query = select(Model).where(Model.provider_id == provider_id)
    if is_active is not None:
        query = query.where(Model.is_active == is_active)
    if model_type:
        query = query.where(Model.model_type == model_type)

    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)

    query = query.order_by(Model.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    models = result.scalars().all()

    return PaginatedResponse(
        items=[ModelResponse.model_validate(m) for m in models],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size,
    )


@router.get("/{provider_id}/models/{model_id}", response_model=ModelResponse)
async def get_model(
    provider_id: int,
    model_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> ModelResponse:
    """Get a specific model."""
    result = await db.execute(
        select(Model)
        .join(Provider)
        .where(Model.id == model_id, Model.provider_id == provider_id, Provider.owner_id == user_id)
    )
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return ModelResponse.model_validate(model)


@router.patch("/{provider_id}/models/{model_id}", response_model=ModelResponse)
async def update_model(
    provider_id: int,
    model_id: int,
    model_data: ModelUpdate,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> ModelResponse:
    """Update a model."""
    result = await db.execute(
        select(Model)
        .join(Provider)
        .where(Model.id == model_id, Model.provider_id == provider_id, Provider.owner_id == user_id)
    )
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    update_data = model_data.model_dump(exclude_unset=True)
    if "model_type" in update_data:
        update_data["model_type"] = update_data["model_type"].value

    for field, value in update_data.items():
        setattr(model, field, value)

    await db.commit()
    await db.refresh(model)
    return ModelResponse.model_validate(model)


@router.delete("/{provider_id}/models/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_model(
    provider_id: int,
    model_id: int,
    db: AsyncSession = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
) -> None:
    """Delete a model."""
    result = await db.execute(
        select(Model)
        .join(Provider)
        .where(Model.id == model_id, Model.provider_id == provider_id, Provider.owner_id == user_id)
    )
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    await db.delete(model)
    await db.commit()