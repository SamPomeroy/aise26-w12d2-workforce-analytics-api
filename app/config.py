from pydantic_settings import BaseSettings
from typing import List
import json


class Settings(BaseSettings):
    """
    application configuration loaded from environment variables
    uses pydantic for validation and type safety
    """
    
    # app metadata
    app_name: str = "Workforce Analytics API"
    app_version: str = "1.0.0"
    debug: bool = True
    environment: str = "development"
    
    # server config
    host: str = "0.0.0.0"
    port: int = 8000
    
    # database
    database_url: str = "sqlite:///./workforce_analytics.db"
    
    # jwt auth
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # redis config
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""
    
    # rate limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 3600
    
    # cors - handle string or list
    cors_origins: str | List[str] = '["http://localhost:3000","http://localhost:8000"]'
    
    # external apis
    bls_api_key: str = ""
    bls_api_url: str = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
    
    # logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    @property
    def cors_origins_list(self) -> List[str]:
        """parse cors origins if they come in as a json string"""
        if isinstance(self.cors_origins, str):
            try:
                return json.loads(self.cors_origins)
            except json.JSONDecodeError:
                return [self.cors_origins]
        return self.cors_origins
    
    @property
    def redis_url(self) -> str:
        """construct redis connection url"""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"


# global settings instance
settings = Settings()
