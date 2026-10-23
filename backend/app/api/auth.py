"""Authentication API endpoints for OIDC flow."""

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.oidc import oidc_client
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
    get_password_hash,
)
from app.models import User, AuditLog
from app.schemas import (
    AuthUrlResponse,
    TokenRequest,
    TokenResponse,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["authentication"])
settings = get_settings()


@router.get("/login", response_model=AuthUrlResponse)
async def login() -> AuthUrlResponse:
    """
    Initiate OIDC authorization code flow with PKCE.
    Returns authorization URL and state for the frontend.
    """
    if not settings.oidc_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OIDC authentication is not configured",
        )

    auth_url, state, code_verifier = oidc_client.get_authorization_url()

    # In production, store code_verifier in secure session/server-side
    # For now, return it to frontend to store in sessionStorage
    return AuthUrlResponse(auth_url=auth_url, state=state)


@router.post("/callback", response_model=TokenResponse)
async def callback(
    request: TokenRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """
    Handle OIDC callback: exchange code for tokens, create/update user, issue JWTs.
    """
    if not settings.oidc_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OIDC authentication is not configured",
        )

    # Exchange authorization code for tokens
    try:
        token_data = await oidc_client.exchange_code(request.code, request.code_verifier)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to exchange code: {str(e)}",
        )

    # Fetch user info
    try:
        user_info = await oidc_client.get_user_info(token_data.access_token)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to fetch user info: {str(e)}",
        )

    # Extract roles from realm_access
    roles = []
    if user_info.realm_access and "roles" in user_info.realm_access:
        roles = user_info.realm_access["roles"]

    # Find or create user
    result = await db.execute(select(User).where(User.oidc_sub == user_info.sub))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            oidc_sub=user_info.sub,
            username=user_info.preferred_username or user_info.sub,
            email=user_info.email,
            full_name=user_info.name,
            roles=roles,
            is_admin="admin" in roles,
        )
        db.add(user)
    else:
        user.username = user_info.preferred_username or user.username
        user.email = user_info.email or user.email
        user.full_name = user_info.name or user.full_name
        user.roles = roles
        user.is_admin = "admin" in roles
        user.last_login = user_info.updated_at if hasattr(user_info, "updated_at") else None

    await db.commit()
    await db.refresh(user)

    # Create JWT tokens
    access_token = create_access_token(
        subject=str(user.id),
        roles=user.roles,
    )
    refresh_token = create_refresh_token(subject=str(user.id))

    # Set HttpOnly cookies
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.environment == "production",
        samesite="lax",
        max_age=settings.access_token_expire_minutes * 60,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.environment == "production",
        samesite="lax",
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
    )

    # Log audit
    audit = AuditLog(
        user_id=user.id,
        action="login",
        resource_type="user",
        resource_id=str(user.id),
        details={"provider": "oidc"},
    )
    db.add(audit)
    await db.commit()

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
        refresh_token=refresh_token,
        id_token=token_data.id_token,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Refresh access token using refresh token."""
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found",
        )

    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    # Issue new tokens
    new_access_token = create_access_token(subject=str(user.id), roles=user.roles)
    new_refresh_token = create_refresh_token(subject=str(user.id))

    response.set_cookie(
        key="access_token",
        value=new_access_token,
        httponly=True,
        secure=settings.environment == "production",
        samesite="lax",
        max_age=settings.access_token_expire_minutes * 60,
    )
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=settings.environment == "production",
        samesite="lax",
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
    )

    return TokenResponse(
        access_token=new_access_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
        refresh_token=new_refresh_token,
    )


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Logout: clear cookies and optionally call Keycloak logout."""
    access_token = request.cookies.get("access_token")
    id_token = None

    if access_token:
        payload = decode_token(access_token)
        if payload:
            user_id = payload.get("sub")
            if user_id:
                audit = AuditLog(
                    user_id=int(user_id),
                    action="logout",
                    resource_type="user",
                    resource_id=user_id,
                )
                db.add(audit)
                await db.commit()

    # Clear cookies
    response.delete_cookie("access_token", httponly=True, secure=settings.environment == "production", samesite="lax")
    response.delete_cookie("refresh_token", httponly=True, secure=settings.environment == "production", samesite="lax")

    # Redirect to Keycloak logout if OIDC enabled
    if settings.oidc_enabled and id_token:
        logout_url = await oidc_client.logout_url(id_token)
        return {"logout_url": logout_url}

    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Get current authenticated user from JWT cookie."""
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    payload = decode_token(access_token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    return UserResponse(
        id=user.id,
        oidc_sub=user.oidc_sub,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        is_admin=user.is_admin,
        roles=user.roles,
        created_at=user.created_at,
    )