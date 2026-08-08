import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application Settings loaded from environment variables or .env file."""
    
    APP_NAME: str = "Minni - AI Safety Assistant"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    
    # Gemini API settings
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.5-flash"
    
    # Session TTL
    SESSION_TTL_MINUTES: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def is_gemini_configured(self) -> bool:
        """Check if Gemini API Key is configured and not placeholder."""
        return bool(
            self.GEMINI_API_KEY 
            and self.GEMINI_API_KEY.strip() 
            and self.GEMINI_API_KEY != "your_gemini_api_key_here"
        )


settings = Settings()
