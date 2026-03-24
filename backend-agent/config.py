#!/usr/bin/env python3
"""
Configuration Module - Enhanced Security for API Key Management
Loads and validates environment variables with proper masking for logs
"""

import os
import logging
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


def mask_api_key(key: Optional[str]) -> str:
    """
    Mask API key for logging - shows only first/last 4 characters
    
    Args:
        key: API key string
        
    Returns:
        Masked string (e.g., "sk-1234...xyz9") or "NOT_SET"
    """
    if not key:
        return "NOT_SET"
    if len(key) < 8:
        return "***"
    return f"{key[:4]}...{key[-4:]}"


def validate_required_env_vars(required_vars: list[str]) -> dict[str, str]:
    """
    Validate that all required environment variables are set
    
    Args:
        required_vars: List of required environment variable names
        
    Returns:
        Dictionary of validated environment variables
        
    Raises:
        RuntimeError: If any required variables are missing
    """
    missing = []
    config = {}
    
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing.append(var)
        else:
            config[var] = value
            logger.info(f"Loaded {var}: {mask_api_key(value)}")
    
    if missing:
        error_msg = f"Missing required environment variables: {', '.join(missing)}"
        logger.error(error_msg)
        raise RuntimeError(
            f"{error_msg}\n"
            f"Please set these in your .env file or environment.\n"
            f"See .env.example for reference."
        )
    
    return config


class Config:
    """Application configuration with secure API key handling"""
    
    def __init__(self):
        # Validate and load required variables
        required = ["OPENAI_API_KEY", "OPENWEATHER_API_KEY"]
        env_vars = validate_required_env_vars(required)
        
        # OpenAI Configuration
        self.OPENAI_API_KEY = env_vars["OPENAI_API_KEY"]
        self.OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
        
        # OpenWeatherMap Configuration
        self.OPENWEATHER_API_KEY = env_vars["OPENWEATHER_API_KEY"]
        
        # Server Configuration
        self.PORT = int(os.getenv("PORT", "8000"))
        self.HOST = os.getenv("HOST", "0.0.0.0")
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        
        # Security Settings
        self.ENABLE_CORS = os.getenv("ENABLE_CORS", "true").lower() == "true"
        self.ALLOWED_ORIGINS = os.getenv(
            "ALLOWED_ORIGINS", 
            "http://localhost:3000,http://localhost:5173"
        ).split(",")
        
        logger.info("Configuration loaded successfully")
        logger.info(f"OpenAI Model: {self.OPENAI_MODEL}")
        logger.info(f"Server Port: {self.PORT}")
        logger.info(f"CORS Enabled: {self.ENABLE_CORS}")
    
    def __repr__(self) -> str:
        """Safe string representation with masked keys"""
        return (
            f"Config(\n"
            f"  OPENAI_API_KEY={mask_api_key(self.OPENAI_API_KEY)},\n"
            f"  OPENWEATHER_API_KEY={mask_api_key(self.OPENWEATHER_API_KEY)},\n"
            f"  OPENAI_MODEL={self.OPENAI_MODEL},\n"
            f"  PORT={self.PORT},\n"
            f"  CORS_ENABLED={self.ENABLE_CORS}\n"
            f")"
        )


# Global configuration instance
try:
    config = Config()
except RuntimeError as e:
    logger.critical(str(e))
    # Don't fail immediately - let the application handle it
    config = None
