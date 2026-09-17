from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.database.session import get_db
from app.database.models import User as UserModel
from app.auth.security import verify_password, create_access_token, create_refresh_token, decode_token
from app.auth.redis_cache import revoke_token
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication & RBAC"])


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: str
    username: str
    patient_id: Optional[str] = None
    practitioner_id: Optional[str] = None


class RefreshRequest(BaseModel):
    refresh_token: str


class UserProfileResponse(BaseModel):
    id: str
    username: str
    role: str
    patient_id: Optional[str] = None
    practitioner_id: Optional[str] = None
    active: bool


async def _authenticate_user(username: str, password: str, db: AsyncSession) -> UserModel:
    stmt = select(UserModel).where(UserModel.username == username)
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


@router.post("/login", response_model=TokenResponse)
async def login_json(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await _authenticate_user(payload.username, payload.password, db)
    token_data = {
        "sub": user.username,
        "role": user.role,
        "patient_id": user.patient_id,
        "practitioner_id": user.practitioner_id
    }
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
        role=user.role,
        username=user.username,
        patient_id=user.patient_id,
        practitioner_id=user.practitioner_id
    )


@router.post("/token", response_model=TokenResponse)
async def login_oauth2_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    user = await _authenticate_user(form_data.username, form_data.password, db)
    token_data = {
        "sub": user.username,
        "role": user.role,
        "patient_id": user.patient_id,
        "practitioner_id": user.practitioner_id
    }
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
        role=user.role,
        username=user.username,
        patient_id=user.patient_id,
        practitioner_id=user.practitioner_id
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    try:
        decoded = decode_token(payload.refresh_token)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid refresh token: {e}")

    if decoded.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type, expected refresh")

    username = decoded.get("sub")
    stmt = select(UserModel).where(UserModel.username == username)
    user = (await db.execute(stmt)).scalars().first()
    if not user or not user.active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    token_data = {
        "sub": user.username,
        "role": user.role,
        "patient_id": user.patient_id,
        "practitioner_id": user.practitioner_id
    }
    return TokenResponse(
        access_token=create_access_token(token_data),
        refresh_token=create_refresh_token(token_data),
        role=user.role,
        username=user.username,
        patient_id=user.patient_id,
        practitioner_id=user.practitioner_id
    )


@router.post("/logout")
async def logout(
    authorization: Optional[str] = Header(None),
    current_user: UserModel = Depends(get_current_user)
):
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
        await revoke_token(token)
    return {"status": "ok", "message": f"Successfully logged out {current_user.username}. Token revoked."}


@router.get("/me", response_model=UserProfileResponse)
async def get_me(current_user: UserModel = Depends(get_current_user)):
    return UserProfileResponse(
        id=current_user.id,
        username=current_user.username,
        role=current_user.role,
        patient_id=current_user.patient_id,
        practitioner_id=current_user.practitioner_id,
        active=current_user.active
    )

