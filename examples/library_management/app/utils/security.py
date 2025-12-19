"""
Security utilities for JWT and password hashing
"""

from datetime import datetime, timedelta
from typing import Optional
import hashlib
import bcrypt
from jose import JWTError, jwt
from config import settings


def hash_password(password: str) -> str:
    """Hash a password using SHA256 + bcrypt"""
    # First hash with SHA256
    senha_bytes = password.encode("utf-8")
    pre_hash = hashlib.sha256(senha_bytes).digest()
    
    # Then hash with bcrypt (with 72-byte limit handled by bcrypt)
    hash_final = bcrypt.hashpw(pre_hash, bcrypt.gensalt())
    return hash_final.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash using SHA256 + bcrypt"""
    # First hash with SHA256
    senha_bytes = plain_password.encode("utf-8")
    pre_hash = hashlib.sha256(senha_bytes).digest()
    
    # Then verify with bcrypt
    return bcrypt.checkpw(pre_hash, hashed_password.encode('utf-8'))


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and verify JWT token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None
