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
        from datetime import datetime
        
        # Check if user exists
        existing_user = await User.findOne({"$or": [{"username": username}, {"email": email}]})
        if existing_user:
            raise ValueError("Username or email already exists")
        
        # Hash password
        password_hash = hash_password(password)
        
        # Create user with all fields
        now = datetime.utcnow()
        user = await User.create(
            username=username,
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            role=role,
            is_active=True,
            created_at=now,
            updated_at=now
        )
        
        return user
    
    @staticmethod
    async def authenticate_user(username: str, password: str) -> Optional[User]:
        """Authenticate user"""
        user = await User.findOne({"username": username})
        
        if not user:
            return None
        
        password_hash = getattr(user, 'password_hash', None)
        if not password_hash or not verify_password(password, password_hash):
            return None
        
        return user
    
    @staticmethod
    def create_token(user: User) -> str:
        """Create JWT token for user"""
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        token_data = {
            "sub": getattr(user, 'username', ''),
            "role": getattr(user, 'role', 'member'),
            "user_id": str(getattr(user, 'id', ''))
        }
        
        access_token = create_access_token(
            data=token_data,
            expires_delta=access_token_expires
        )
        
        return access_token
