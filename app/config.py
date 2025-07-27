"""
Configuration management for ELAMS
"""

import os
from typing import List, Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    app_name: str = Field(default="ELAMS", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Server
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    workers: int = Field(default=4, env="WORKERS")
    
    # Database
    database_url: str = Field(..., env="DATABASE_URL")
    redis_url: str = Field(..., env="REDIS_URL")
    
    # Security
    secret_key: str = Field(..., env="SECRET_KEY")
    jwt_secret_key: str = Field(..., env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="RS256", env="JWT_ALGORITHM")
    jwt_expire_minutes: int = Field(default=30, env="JWT_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=30, env="REFRESH_TOKEN_EXPIRE_DAYS")
    
    # CORS
    cors_origins: List[str] = Field(
        default=["http://localhost:4200", "http://localhost:8080"], 
        env="CORS_ORIGINS"
    )
    cors_credentials: bool = Field(default=True, env="CORS_CREDENTIALS")
    cors_methods: List[str] = Field(
        default=["GET", "POST", "PUT", "DELETE", "OPTIONS"], 
        env="CORS_METHODS"
    )
    cors_headers: List[str] = Field(default=["*"], env="CORS_HEADERS")
    
    # Rate Limiting
    rate_limit_requests: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(default=60, env="RATE_LIMIT_WINDOW")
    
    # Session
    session_timeout_minutes: int = Field(default=480, env="SESSION_TIMEOUT_MINUTES")
    max_concurrent_sessions: int = Field(default=5, env="MAX_CONCURRENT_SESSIONS")
    session_secure: bool = Field(default=True, env="SESSION_SECURE")
    session_httponly: bool = Field(default=True, env="SESSION_HTTPONLY")
    
    # Password Policy
    password_min_length: int = Field(default=12, env="PASSWORD_MIN_LENGTH")
    password_require_uppercase: bool = Field(default=True, env="PASSWORD_REQUIRE_UPPERCASE")
    password_require_lowercase: bool = Field(default=True, env="PASSWORD_REQUIRE_LOWERCASE")
    password_require_numbers: bool = Field(default=True, env="PASSWORD_REQUIRE_NUMBERS")
    password_require_special: bool = Field(default=True, env="PASSWORD_REQUIRE_SPECIAL")
    password_history_count: int = Field(default=12, env="PASSWORD_HISTORY_COUNT")
    password_expiry_days: int = Field(default=90, env="PASSWORD_EXPIRY_DAYS")
    
    # MFA
    mfa_enabled: bool = Field(default=True, env="MFA_ENABLED")
    mfa_issuer_name: str = Field(default="ELAMS", env="MFA_ISSUER_NAME")
    totp_window: int = Field(default=30, env="TOTP_WINDOW")
    backup_codes_count: int = Field(default=10, env="BACKUP_CODES_COUNT")
    
    # Email
    smtp_host: str = Field(default="", env="SMTP_HOST")
    smtp_port: int = Field(default=587, env="SMTP_PORT")
    smtp_username: str = Field(default="", env="SMTP_USERNAME")
    smtp_password: str = Field(default="", env="SMTP_PASSWORD")
    smtp_tls: bool = Field(default=True, env="SMTP_TLS")
    smtp_ssl: bool = Field(default=False, env="SMTP_SSL")
    email_from: str = Field(default="noreply@elams.local", env="EMAIL_FROM")
    email_from_name: str = Field(default="ELAMS Security", env="EMAIL_FROM_NAME")
    
    # SMS (Twilio)
    twilio_account_sid: str = Field(default="", env="TWILIO_ACCOUNT_SID")
    twilio_auth_token: str = Field(default="", env="TWILIO_AUTH_TOKEN")
    twilio_phone_number: str = Field(default="", env="TWILIO_PHONE_NUMBER")
    
    # LDAP
    ldap_enabled: bool = Field(default=False, env="LDAP_ENABLED")
    ldap_server: str = Field(default="", env="LDAP_SERVER")
    ldap_port: int = Field(default=389, env="LDAP_PORT")
    ldap_use_ssl: bool = Field(default=False, env="LDAP_USE_SSL")
    ldap_bind_dn: str = Field(default="", env="LDAP_BIND_DN")
    ldap_bind_password: str = Field(default="", env="LDAP_BIND_PASSWORD")
    ldap_user_search_base: str = Field(default="", env="LDAP_USER_SEARCH_BASE")
    ldap_group_search_base: str = Field(default="", env="LDAP_GROUP_SEARCH_BASE")
    
    # OAuth2
    oauth2_google_client_id: str = Field(default="", env="OAUTH2_GOOGLE_CLIENT_ID")
    oauth2_google_client_secret: str = Field(default="", env="OAUTH2_GOOGLE_CLIENT_SECRET")
    oauth2_microsoft_client_id: str = Field(default="", env="OAUTH2_MICROSOFT_CLIENT_ID")
    oauth2_microsoft_client_secret: str = Field(default="", env="OAUTH2_MICROSOFT_CLIENT_SECRET")
    
    # Audit
    audit_enabled: bool = Field(default=True, env="AUDIT_ENABLED")
    audit_retention_days: int = Field(default=2555, env="AUDIT_RETENTION_DAYS")
    audit_log_level: str = Field(default="INFO", env="AUDIT_LOG_LEVEL")
    
    # Monitoring
    prometheus_enabled: bool = Field(default=True, env="PROMETHEUS_ENABLED")
    prometheus_port: int = Field(default=9091, env="PROMETHEUS_PORT")
    health_check_enabled: bool = Field(default=True, env="HEALTH_CHECK_ENABLED")
    
    # File Upload
    max_upload_size: int = Field(default=10485760, env="MAX_UPLOAD_SIZE")  # 10MB
    allowed_file_types: List[str] = Field(
        default=["csv", "xlsx", "json"], 
        env="ALLOWED_FILE_TYPES"
    )
    upload_path: str = Field(default="/app/uploads", env="UPLOAD_PATH")
    
    # Compliance
    gdpr_enabled: bool = Field(default=True, env="GDPR_ENABLED")
    data_retention_days: int = Field(default=2555, env="DATA_RETENTION_DAYS")
    pii_encryption_enabled: bool = Field(default=True, env="PII_ENCRYPTION_ENABLED")
    
    # API
    api_title: str = Field(default="ELAMS API", env="API_TITLE")
    api_description: str = Field(
        default="Enterprise Logical Access Management System API", 
        env="API_DESCRIPTION"
    )
    api_version: str = Field(default="1.0.0", env="API_VERSION")
    api_docs_url: str = Field(default="/docs", env="API_DOCS_URL")
    api_redoc_url: str = Field(default="/redoc", env="API_REDOC_URL")
    
    # Cache
    cache_ttl: int = Field(default=3600, env="CACHE_TTL")
    cache_max_size: int = Field(default=10000, env="CACHE_MAX_SIZE")
    
    # Celery
    celery_broker_url: str = Field(default="", env="CELERY_BROKER_URL")
    celery_result_backend: str = Field(default="", env="CELERY_RESULT_BACKEND")
    
    # Logging
    log_format: str = Field(default="json", env="LOG_FORMAT")
    log_file_path: str = Field(default="/app/logs/elams.log", env="LOG_FILE_PATH")
    log_max_size: str = Field(default="100MB", env="LOG_MAX_SIZE")
    log_backup_count: int = Field(default=10, env="LOG_BACKUP_COUNT")
    
    @validator("environment")
    def validate_environment(cls, v):
        if v not in ["development", "staging", "production"]:
            raise ValueError("Environment must be development, staging, or production")
        return v
    
    @validator("log_level")
    def validate_log_level(cls, v):
        if v not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            raise ValueError("Log level must be DEBUG, INFO, WARNING, ERROR, or CRITICAL")
        return v
    
    @validator("jwt_algorithm")
    def validate_jwt_algorithm(cls, v):
        if v not in ["HS256", "HS384", "HS512", "RS256", "RS384", "RS512"]:
            raise ValueError("Invalid JWT algorithm")
        return v
    
    @validator("secret_key")
    def validate_secret_key(cls, v):
        if len(v) < 32:
            raise ValueError("Secret key must be at least 32 characters long")
        return v
    
    @property
    def is_development(self) -> bool:
        return self.environment == "development"
    
    @property
    def is_production(self) -> bool:
        return self.environment == "production"
    
    @property
    def is_staging(self) -> bool:
        return self.environment == "staging"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()