"""
Multi-Factor Authentication models
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Boolean, Column, DateTime, String, Text, Integer, 
    ForeignKey, JSON, Enum as SQLEnum, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.database import Base


class MFADeviceType(str, enum.Enum):
    """MFA device types"""
    TOTP = "totp"              # Time-based One-Time Password (Google Authenticator, etc.)
    SMS = "sms"                # SMS-based authentication
    EMAIL = "email"            # Email-based authentication
    HARDWARE = "hardware"      # Hardware tokens (YubiKey, etc.)
    BACKUP_CODES = "backup_codes"  # One-time backup codes
    PUSH = "push"              # Push notifications


class MFADeviceStatus(str, enum.Enum):
    """MFA device status"""
    PENDING = "pending"        # Awaiting activation
    ACTIVE = "active"          # Active and ready for use
    SUSPENDED = "suspended"    # Temporarily disabled
    REVOKED = "revoked"        # Permanently disabled


class MFADevice(Base):
    """
    Multi-Factor Authentication device registration
    """
    __tablename__ = "mfa_devices"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Device identification
    device_type = Column(SQLEnum(MFADeviceType), nullable=False)
    device_name = Column(String(100), nullable=False)      # User-friendly name
    device_identifier = Column(String(255), nullable=True)  # Phone number, email, etc.
    
    # Device status and settings
    status = Column(SQLEnum(MFADeviceStatus), default=MFADeviceStatus.PENDING, nullable=False)
    is_primary = Column(Boolean, default=False, nullable=False)
    is_backup = Column(Boolean, default=False, nullable=False)
    
    # TOTP-specific fields
    secret_key = Column(String(255), nullable=True)        # Base32-encoded secret
    qr_code_url = Column(String(500), nullable=True)       # QR code for setup
    
    # SMS/Email-specific fields
    contact_info = Column(String(255), nullable=True)      # Phone/email for delivery
    
    # Hardware token fields
    serial_number = Column(String(100), nullable=True)
    hardware_type = Column(String(50), nullable=True)      # yubikey, rsa, etc.
    
    # Backup codes (stored encrypted)
    backup_codes = Column(JSON, default=list, nullable=False)
    backup_codes_used = Column(JSON, default=list, nullable=False)
    
    # Usage tracking
    last_used = Column(DateTime(timezone=True), nullable=True)
    usage_count = Column(Integer, default=0, nullable=False)
    failure_count = Column(Integer, default=0, nullable=False)
    
    # Verification status
    verified = Column(Boolean, default=False, nullable=False)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    verification_code = Column(String(10), nullable=True)   # For initial setup
    
    # Security settings
    rate_limit_window = Column(Integer, default=300, nullable=False)  # 5 minutes
    max_attempts_per_window = Column(Integer, default=5, nullable=False)
    
    # Metadata
    device_metadata = Column(JSON, default=dict, nullable=False)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="mfa_devices")
    created_by_user = relationship("User", foreign_keys=[created_by])
    mfa_tokens = relationship("MFAToken", back_populates="device", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_mfa_device_user", "user_id"),
        Index("idx_mfa_device_type", "device_type"),
        Index("idx_mfa_device_status", "status"),
        Index("idx_mfa_device_primary", "user_id", "is_primary"),
        Index("idx_mfa_device_contact", "contact_info"),
        UniqueConstraint("user_id", "device_name", name="uq_user_device_name"),
    )
    
    def __repr__(self):
        return f"<MFADevice(user_id='{self.user_id}', type='{self.device_type}', name='{self.device_name}', status='{self.status}')>"


class MFATokenType(str, enum.Enum):
    """MFA token types"""
    VERIFICATION = "verification"   # For device setup/verification
    AUTHENTICATION = "authentication"  # For login authentication
    RECOVERY = "recovery"          # For account recovery


class MFATokenStatus(str, enum.Enum):
    """MFA token status"""
    PENDING = "pending"
    USED = "used"
    EXPIRED = "expired"
    REVOKED = "revoked"


class MFAToken(Base):
    """
    MFA tokens for various authentication flows
    """
    __tablename__ = "mfa_tokens"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    device_id = Column(UUID(as_uuid=True), ForeignKey("mfa_devices.id"), nullable=True)
    
    # Token details
    token_type = Column(SQLEnum(MFATokenType), nullable=False)
    token_value = Column(String(255), nullable=False, index=True)  # The actual token/code
    token_hash = Column(String(255), nullable=False)              # Hashed version for verification
    
    # Token status and lifecycle
    status = Column(SQLEnum(MFATokenStatus), default=MFATokenStatus.PENDING, nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    
    # Usage tracking
    attempts = Column(Integer, default=0, nullable=False)
    max_attempts = Column(Integer, default=3, nullable=False)
    
    # Context information
    ip_address = Column(String(45), nullable=True)         # IPv4/IPv6
    user_agent = Column(Text, nullable=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("user_sessions.id"), nullable=True)
    
    # Delivery information (for SMS/Email)
    delivery_method = Column(String(50), nullable=True)
    delivery_address = Column(String(255), nullable=True)
    delivery_status = Column(String(50), nullable=True)
    delivery_attempts = Column(Integer, default=0, nullable=False)
    
    # Additional metadata
    metadata = Column(JSON, default=dict, nullable=False)
    
    # Relationships
    user = relationship("User")
    device = relationship("MFADevice", back_populates="mfa_tokens")
    session = relationship("UserSession")
    
    __table_args__ = (
        Index("idx_mfa_token_user", "user_id"),
        Index("idx_mfa_token_device", "device_id"),
        Index("idx_mfa_token_type", "token_type"),
        Index("idx_mfa_token_status", "status"),
        Index("idx_mfa_token_expires", "expires_at"),
        Index("idx_mfa_token_value", "token_value"),
        Index("idx_mfa_token_hash", "token_hash"),
    )
    
    @property
    def is_valid(self) -> bool:
        """Check if token is still valid"""
        now = datetime.utcnow()
        return (
            self.status == MFATokenStatus.PENDING and
            self.expires_at > now and
            self.attempts < self.max_attempts
        )
    
    def __repr__(self):
        return f"<MFAToken(user_id='{self.user_id}', type='{self.token_type}', status='{self.status}')>"


class MFAAttempt(Base):
    """
    MFA authentication attempt logging
    """
    __tablename__ = "mfa_attempts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    device_id = Column(UUID(as_uuid=True), ForeignKey("mfa_devices.id"), nullable=True)
    token_id = Column(UUID(as_uuid=True), ForeignKey("mfa_tokens.id"), nullable=True)
    
    # Attempt details
    attempt_type = Column(String(50), nullable=False)      # login, setup, recovery
    provided_code = Column(String(255), nullable=True)     # What user provided (hashed)
    success = Column(Boolean, nullable=False)
    failure_reason = Column(String(200), nullable=True)
    
    # Context
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("user_sessions.id"), nullable=True)
    
    # Timing
    attempted_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    
    # Security context
    risk_score = Column(Integer, default=0, nullable=False)  # 0-100
    anomaly_detected = Column(Boolean, default=False, nullable=False)
    
    # Additional data
    metadata = Column(JSON, default=dict, nullable=False)
    
    # Relationships
    user = relationship("User")
    device = relationship("MFADevice")
    token = relationship("MFAToken")
    session = relationship("UserSession")
    
    __table_args__ = (
        Index("idx_mfa_attempt_user", "user_id", "attempted_at"),
        Index("idx_mfa_attempt_device", "device_id"),
        Index("idx_mfa_attempt_success", "success"),
        Index("idx_mfa_attempt_timestamp", "attempted_at"),
        Index("idx_mfa_attempt_ip", "ip_address"),
        Index("idx_mfa_attempt_risk", "risk_score"),
    )
    
    def __repr__(self):
        return f"<MFAAttempt(user_id='{self.user_id}', success='{self.success}', attempted_at='{self.attempted_at}')>"