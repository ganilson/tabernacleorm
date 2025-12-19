"""
Configuration for Library Management System
"""

import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    APP_NAME: str = "Library Management System - TABERNACLEORM-AO"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Database
    # SQLite (default)
    DATABASE_URL: str = "mongodb://localhost:27017/library"
    
    # MongoDB options
    # Single instance: mongodb://localhost:27017/library
    # Replica set: mongodb://host1:27017,host2:27017,host3:27017/library?replicaSet=rs0
    # MongoDB Atlas: mongodb+srv://user:pass@cluster.mongodb.net/library?retryWrites=true&w=majority
    
    # MongoDB Replica Set Configuration
    MONGODB_REPLICA_SET: str = ""  # e.g., "rs0"
    MONGODB_READ_PREFERENCE: str = "secondaryPreferred"  # primary, secondary, secondaryPreferred
    MONGODB_WRITE_CONCERN: int = 1  # 0 = no acknowledgment, 1 = acknowledged, majority
    
    # JWT
    SECRET_KEY: str = "ganilson"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Loan Settings
    DEFAULT_LOAN_DAYS: int = 14
    MAX_LOANS_PER_USER: int = 5
    FINE_PER_DAY: float = 0.50
    
    class Config:
        env_file = ".env"


settings = Settings()
