from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List, Callable

from app.database.session import get_db
from app.database.models import User as UserModel
from app.auth.security import decode_token
from app.auth.redis_cache import is_token_revoked

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
) -> UserModel:
    # Allow Bearer token from either OAuth2 scheme or Authorization header
    auth_token = token
    if not auth_token and authorization:
        if authorization.lower().startswith("bearer "):
            auth_token = authorization.split(" ", 1)[1].strip()

    if not auth_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required: Missing Bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check Redis blacklist
    if await is_token_revoked(auth_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Decode and validate token
    try:
        payload = decode_token(auth_token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    username: Optional[str] = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject identifier",
            headers={"WWW-Authenticate": "Bearer"},
        )

    stmt = select(UserModel).where(UserModel.username == username)
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user or not user.active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or account is deactivated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def require_role(*allowed_roles: str) -> Callable:
    """Dependency that checks if the authenticated user has one of the allowed roles."""
    async def role_checker(current_user: UserModel = Depends(get_current_user)) -> UserModel:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: Role '{current_user.role}' is not authorized. Allowed roles: {list(allowed_roles)}"
            )
        return current_user
    return role_checker


def verify_patient_access(patient_id: str, current_user: UserModel):
    """Ensure that PATIENT role users can only access their own records."""
    if current_user.role == "PATIENT":
        clean_target = patient_id.replace("Patient/", "")
        user_patient = (current_user.patient_id or "").replace("Patient/", "")
        if clean_target != user_patient:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: Patients can only access their own health records."
            )

