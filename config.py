import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

# Since your .env is in the root (based on your folder structure image)
BASE_DIR = Path(__file__).resolve().parent

class Settings(BaseSettings):
    # Project Metadata
    PROJECT_NAME: str 
    
    # API Keys & Secrets
    PINECONE_API_KEY: str
    PINECONE_ENVIRONMENT: str 
    
    # Database Configuration
    DATABASE_URL: str 

    # Pydantic Settings Config
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

# Singleton instance to be imported across the project
settings = Settings()