"""
Authentication Controller
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from services.auth_service import AuthService

router = APIRouter()


class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str
    role: str = "member"


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest):
    """Register a new user"""
    try:
        user = await AuthService.register_user(
            username=request.username,
            email=request.email,
            password=request.password,
            full_name=request.full_name,
            role=request.role
        )
        
        token = AuthService.create_token(user)
        
        user_dict = {
            "id": str(getattr(user, 'id', '')),
            "username": getattr(user, 'username', ''),
            "email": getattr(user, 'email', ''),
            "full_name": getattr(user, 'full_name', ''),
            "role": getattr(user, 'role', 'member')
        }
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": user_dict
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """Login user"""
    user = await AuthService.authenticate_user(request.username, request.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    token = AuthService.create_token(user)
    
    user_dict = {
        "id": str(getattr(user, 'id', '')),
        "username": getattr(user, 'username', ''),
        "email": getattr(user, 'email', ''),
        "full_name": getattr(user, 'full_name', ''),
        "role": getattr(user, 'role', 'member')
    }
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user_dict
    }
