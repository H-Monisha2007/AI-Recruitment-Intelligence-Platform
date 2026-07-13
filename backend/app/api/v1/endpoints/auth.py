"""
Auth endpoints — register, login, refresh, me.
"""
from __future__ import annotations
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.services import auth_service
from app.auth.dependencies import get_current_active_user
from app.database.models import User

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED,
             summary="Register a new user", tags=["auth"])
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    user = await auth_service.register_user(db, data)
    return user


@router.post("/login", response_model=TokenResponse, summary="Login and receive JWT tokens", tags=["auth"])
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await auth_service.authenticate_user(db, data.email, data.password)
    return auth_service.create_token_response(user)


@router.post("/refresh", response_model=TokenResponse, summary="Refresh access token", tags=["auth"])
async def refresh(refresh_token: str, db: AsyncSession = Depends(get_db)):
    return await auth_service.refresh_user_token(db, refresh_token)


@router.get("/me", response_model=UserResponse, summary="Get current authenticated user", tags=["auth"])
async def get_me(current_user: User = Depends(get_current_active_user)):
    return current_user