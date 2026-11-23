from datetime import timedelta
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, status, Body
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
import structlog

from app.services.auth.service import auth_service

logger = structlog.get_logger()

router = APIRouter(prefix="/auth", tags=["authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    user_id: Optional[str] = None
    email: Optional[str] = None


class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: Optional[str] = None


class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    full_name: Optional[str] = None
    is_active: bool
    is_superuser: bool
    created_at: str
    last_login: Optional[str] = None

    class Config:
        from_attributes = True


class APIKeyCreate(BaseModel):
    name: str
    expires_days: Optional[int] = None


class APIKeyResponse(BaseModel):
    key: str
    id: str
    name: str
    prefix: str
    created_at: str
    expires_at: Optional[str] = None

    class Config:
        from_attributes = True


class APIKeyListResponse(BaseModel):
    id: str
    name: str
    prefix: str
    is_active: bool
    created_at: str
    expires_at: Optional[str] = None
    last_used: Optional[str] = None

    class Config:
        from_attributes = True


async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserResponse:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = auth_service.decode_token(token)
    if payload is None:
        raise credentials_exception
    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    user = auth_service.get_user_by_id(user_id)
    if user is None:
        raise credentials_exception
    
    return UserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        is_active=user.is_active,
        is_superuser=user.is_superuser,
        created_at=user.created_at.isoformat() if user.created_at else "",
        last_login=user.last_login.isoformat() if user.last_login else None,
    )


async def get_current_active_user(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate):
    try:
        user = auth_service.create_user(
            email=user_data.email,
            username=user_data.username,
            password=user_data.password,
            full_name=user_data.full_name,
        )
        return UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            created_at=user.created_at.isoformat() if user.created_at else "",
            last_login=user.last_login.isoformat() if user.last_login else None,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = auth_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=30)
    access_token = auth_service.create_access_token(
        data={"sub": user.id, "email": user.email},
        expires_delta=access_token_expires,
    )
    
    auth_service.update_last_login(user.id)
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=30 * 60,
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: UserResponse = Depends(get_current_active_user)):
    return current_user


@router.post("/api-keys", response_model=APIKeyResponse)
async def create_api_key(
    key_data: APIKeyCreate,
    current_user: UserResponse = Depends(get_current_active_user),
):
    raw_key, api_key = auth_service.create_api_key(
        user_id=current_user.id,
        name=key_data.name,
        expires_days=key_data.expires_days,
    )
    
    return APIKeyResponse(
        key=raw_key,
        id=api_key.id,
        name=api_key.name,
        prefix=api_key.prefix,
        created_at=api_key.created_at.isoformat() if api_key.created_at else "",
        expires_at=api_key.expires_at.isoformat() if api_key.expires_at else None,
    )


@router.get("/api-keys", response_model=list[APIKeyListResponse])
async def list_api_keys(current_user: UserResponse = Depends(get_current_active_user)):
    api_keys = auth_service.list_api_keys(current_user.id)
    return [
        APIKeyListResponse(
            id=k.id,
            name=k.name,
            prefix=k.prefix,
            is_active=k.is_active,
            created_at=k.created_at.isoformat() if k.created_at else "",
            expires_at=k.expires_at.isoformat() if k.expires_at else None,
            last_used=k.last_used.isoformat() if k.last_used else None,
        )
        for k in api_keys
    ]


@router.delete("/api-keys/{key_id}")
async def revoke_api_key(
    key_id: str,
    current_user: UserResponse = Depends(get_current_active_user),
):
    success = auth_service.revoke_api_key(current_user.id, key_id)
    if not success:
        raise HTTPException(status_code=404, detail="API key not found")
    return {"message": "API key revoked"}