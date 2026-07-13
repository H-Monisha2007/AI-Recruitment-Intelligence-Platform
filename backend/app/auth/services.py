import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.schemas import UserCreate
from app.database.models import User
from app.core.security import hash_password, verify_password
from app.repositories.user_repository import UserRepository

class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)

    async def register_user(self, user_in: UserCreate) -> User:
        db_user = await self.user_repo.get_by_email(user_in.email)
        if db_user:
            raise Exception("User already exists")
        
        new_user = User(
            id=str(uuid.uuid4()),
            email=user_in.email,
            full_name=user_in.full_name,
            hashed_password=hash_password(user_in.password),
            role=user_in.role
        )
        return await self.user_repo.create(new_user)

    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        user = await self.user_repo.get_by_email(email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
