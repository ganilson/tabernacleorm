"""
Authentication Service
"""

from datetime import timedelta
from typing import Optional
from models import User
from utils.security import hash_password, verify_password, create_access_token
from config import settings


class AuthService:
    """Service for authentication operations"""
    
    @staticmethod
    async def register_user(username: str, email: str, password: str, full_name: str, role: str = "member") -> User:
        """Register a new user"""
        # Check if user exists
        existing_user = await User.findOne({"$or": [{"username": username}, {"email": email}]})
        if existing_user:
            raise ValueError("Username or email already exists")
        
        # Hash password
        password_hash = hash_password(password)
        
        # Create user
        user = await User.create(
            username=username,
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            role=role
        )
        
        return user
    
    @staticmethod
    async def authenticate_user(username: str, password: str) -> Optional[User]:
        """Authenticate user"""
        user = await User.findOne({"username": username})
        
        if not user:
            return None
        
        if not verify_password(password, user.password_hash):
            return None
        
        return user
    
    @staticmethod
    def create_token(user: User) -> str:
        """Create JWT token for user"""
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        token_data = {
            "sub": user.username,
            "role": user.role,
            "user_id": str(user.id)
        }
        
        access_token = create_access_token(
            data=token_data,
            expires_delta=access_token_expires
        )
        
        return access_token
