from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import authenticate_user, create_access_token, get_current_user, hash_password, require_admin
from app.models.user import User
from app.schemas.auth import AdminCreateRequest, LoginRequest, TokenResponse, UserOut

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, session: AsyncSession = Depends(get_session)) -> TokenResponse:
    user = await authenticate_user(session, data.username, data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
    token = create_access_token(subject=str(user.id), role=user.role)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)) -> UserOut:
    return UserOut(
        id=current_user.id,
        username=current_user.username,
        role=current_user.role,
        is_active=current_user.is_active,
    )


@router.post("/admins", response_model=UserOut, dependencies=[Depends(require_admin)])
async def create_admin(data: AdminCreateRequest, session: AsyncSession = Depends(get_session)) -> UserOut:
    existing = (await session.execute(select(User).where(User.username == data.username))).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists")

    user = User(
        username=data.username,
        password_hash=hash_password(data.password),
        role="admin",
        is_active=True,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return UserOut(id=user.id, username=user.username, role=user.role, is_active=user.is_active)
