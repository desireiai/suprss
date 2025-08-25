# core/config.py
import json
from pydantic import BaseSettings, EmailStr, HttpUrl, PostgresDsn, validator
from typing import List, Optional, Dict, Any
import secrets
from datetime import timedelta

class Settings(BaseSettings):
    """Configuration de l'application SUPRSS"""
    
    # Application
    APP_NAME: str = "SUPRSS"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"  # development, staging, production
    DEBUG: bool = True
    
    # API
    API_PREFIX: str = "/api"
    API_RATE_LIMIT: int = 100  # Requêtes par minute
    
    # Database
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "mypassword"
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str = "suprss_bd"
    
    DATABASE_URL: Optional[PostgresDsn] = None
    
    @validator("DATABASE_URL", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql",
            user=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_HOST"),
            port=values.get("POSTGRES_PORT"),
            path=f"/{values.get('POSTGRES_DB') or ''}",
        )
    
    # Redis
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    REDIS_URL: Optional[str] = None
    
    @validator("REDIS_URL", pre=True)
    def assemble_redis_connection(cls, v: Optional[str], values: Dict[str, Any]) -> str:
        if isinstance(v, str):
            return v
        password = values.get("REDIS_PASSWORD")
        if password:
            return f"redis://:{password}@{values.get('REDIS_HOST')}:{values.get('REDIS_PORT')}/{values.get('REDIS_DB')}"
        return f"redis://{values.get('REDIS_HOST')}:{values.get('REDIS_PORT')}/{values.get('REDIS_DB')}"
    
    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS: int = 24
    PASSWORD_RESET_TOKEN_EXPIRE_HOURS: int = 1
    
    # Bcrypt
    BCRYPT_ROUNDS: int = 12
    
    # # CORS
    # CORS_ORIGINS: List[str] = [
    #     "http://localhost",
    #     "http://localhost:3000",
    #     "http://localhost:8000",
    #     "http://localhost:8080"
    # ]
    # ALLOWED_HOSTS: List[str] = ["*"]

    # @validator("CORS_ORIGINS", pre=True)
    # def assemble_cors_origins(cls, v):
    #     if isinstance(v, str):
    #         # essaie de parser la chaîne comme JSON
    #         try:
    #             parsed = json.loads(v)
    #             if isinstance(parsed, list):
    #                 return parsed
    #         except json.JSONDecodeError:
    #             # Sinon, traite comme chaîne CSV
    #             return [i.strip() for i in v.split(",")]
    #     elif isinstance(v, list):
    #         return v
    #     raise ValueError("CORS_ORIGINS doit être une liste ou une chaîne JSON/virgules.")
    
    # Email
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: EmailStr = "noreply@suprss.com"
    SMTP_FROM_NAME: str = "SUPRSS"
    SMTP_TLS: bool = True
    SMTP_SSL: bool = False
    EMAIL_ENABLED: bool = False
    
    @validator("EMAIL_ENABLED", pre=True)
    def validate_email_config(cls, v: bool, values: Dict[str, Any]) -> bool:
        if v and not (values.get("SMTP_USER") and values.get("SMTP_PASSWORD")):
            return False
        return v
    
    # RSS Feed
    RSS_USER_AGENT: str = "SUPRSS/1.0 (+https://github.com/desireiai/suprss)"
    RSS_TIMEOUT: int = 30  # Secondes
    RSS_MAX_ENTRIES_PER_FEED: int = 100
    RSS_DEFAULT_UPDATE_FREQUENCY_HOURS: int = 6
    RSS_MIN_UPDATE_FREQUENCY_HOURS: int = 1
    RSS_MAX_UPDATE_FREQUENCY_HOURS: int = 168  # 1 semaine
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10 MB
    ALLOWED_UPLOAD_EXTENSIONS: List[str] = [".opml", ".xml", ".json", ".csv"]
    
    # Cache
    CACHE_TTL: int = 300  # 5 minutes
    CACHE_ENABLED: bool = True
    
    # Search
    SEARCH_MIN_LENGTH: int = 2
    SEARCH_MAX_LENGTH: int = 200
    SEARCH_MAX_RESULTS: int = 100
    ENABLE_FULL_TEXT_SEARCH: bool = True
    
    # WebSocket
    WS_MESSAGE_QUEUE_SIZE: int = 100
    WS_HEARTBEAT_INTERVAL: int = 30  # Secondes
    
    # OAuth2 Providers
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: Optional[str] = None
    
    MICROSOFT_CLIENT_ID: Optional[str] = None
    MICROSOFT_CLIENT_SECRET: Optional[str] = None
    MICROSOFT_REDIRECT_URI: Optional[str] = None
    
    GITHUB_CLIENT_ID: Optional[str] = None
    GITHUB_CLIENT_SECRET: Optional[str] = None
    GITHUB_REDIRECT_URI: Optional[str] = None
    
    # Monitoring
    ENABLE_METRICS: bool = True
    METRICS_ENDPOINT: str = "/metrics"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: Optional[str] = None
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    RATE_LIMIT_PER_DAY: int = 10000
    
    # Data Retention
    ARTICLE_RETENTION_DAYS: int = 90
    NOTIFICATION_RETENTION_DAYS: int = 30
    SEARCH_HISTORY_RETENTION_DAYS: int = 30
    
    # Features Flags
    FEATURE_OAUTH2_LOGIN: bool = False
    FEATURE_WEBSOCKET_CHAT: bool = True
    FEATURE_EMAIL_NOTIFICATIONS: bool = False
    FEATURE_EXPORT_IMPORT: bool = True
    FEATURE_ADVANCED_SEARCH: bool = True
    
    # Scheduler
    SCHEDULER_ENABLED: bool = True
    SCHEDULER_TIMEZONE: str = "Europe/Paris"
    
    # Sentry (Error Tracking)
    SENTRY_DSN: Optional[str] = None
    SENTRY_ENVIRONMENT: Optional[str] = None
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        
    def get_oauth_provider_config(self, provider: str) -> Dict[str, str]:
        """Récupère la configuration OAuth pour un provider donné"""
        providers = {
            "google": {
                "client_id": self.GOOGLE_CLIENT_ID,
                "client_secret": self.GOOGLE_CLIENT_SECRET,
                "redirect_uri": self.GOOGLE_REDIRECT_URI,
                "authorize_url": "https://accounts.google.com/o/oauth2/v2/auth",
                "token_url": "https://oauth2.googleapis.com/token",
                "userinfo_url": "https://www.googleapis.com/oauth2/v1/userinfo"
            },
            "microsoft": {
                "client_id": self.MICROSOFT_CLIENT_ID,
                "client_secret": self.MICROSOFT_CLIENT_SECRET,
                "redirect_uri": self.MICROSOFT_REDIRECT_URI,
                "authorize_url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
                "token_url": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
                "userinfo_url": "https://graph.microsoft.com/v1.0/me"
            },
            "github": {
                "client_id": self.GITHUB_CLIENT_ID,
                "client_secret": self.GITHUB_CLIENT_SECRET,
                "redirect_uri": self.GITHUB_REDIRECT_URI,
                "authorize_url": "https://github.com/login/oauth/authorize",
                "token_url": "https://github.com/login/oauth/access_token",
                "userinfo_url": "https://api.github.com/user"
            }
        }
        
        return providers.get(provider, {})
    
    def is_production(self) -> bool:
        """Vérifie si l'environnement est en production"""
        return self.ENVIRONMENT == "production"
    
    def is_development(self) -> bool:
        """Vérifie si l'environnement est en développement"""
        return self.ENVIRONMENT == "development"
    
    def get_database_url_sync(self) -> str:
        """Retourne l'URL de la base de données pour SQLAlchemy synchrone"""
        return str(self.DATABASE_URL).replace("postgresql://", "postgresql+psycopg2://")
    
    def get_database_url_async(self) -> str:
        """Retourne l'URL de la base de données pour SQLAlchemy asynchrone"""
        return str(self.DATABASE_URL).replace("postgresql://", "postgresql+asyncpg://")

# Instance globale des settings
settings = Settings()