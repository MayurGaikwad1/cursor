"""
Session management models
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Boolean, Column, DateTime, String, Text, Integer, 
    ForeignKey, JSON, Enum as SQLEnum, Index
)
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.database import Base


class SessionStatus(str, enum.Enum):
    """Session status"""
    ACTIVE = "active"
    EXPIRED = "expired"
    TERMINATED = "terminated"
    REVOKED = "revoked"


class UserSession(Base):
    """
    User session tracking model
    """
    __tablename__ = "user_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    refresh_token = Column(String(255), unique=True, nullable=True, index=True)
    
    # Session details
    status = Column(SQLEnum(SessionStatus), default=SessionStatus.ACTIVE, nullable=False)
    ip_address = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)
    device_fingerprint = Column(String(255), nullable=True)
    
    # Geographic information
    country = Column(String(100), nullable=True)
    region = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    timezone = Column(String(50), nullable=True)
    
    # Session lifecycle
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    last_activity = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    terminated_at = Column(DateTime(timezone=True), nullable=True)
    
    # Security flags
    is_suspicious = Column(Boolean, default=False, nullable=False)
    risk_score = Column(Integer, default=0, nullable=False)  # 0-100
    mfa_verified = Column(Boolean, default=False, nullable=False)
    
    # Session metadata
    login_method = Column(String(50), nullable=True)  # password, sso, mfa, etc.
    client_application = Column(String(100), nullable=True)
    session_data = Column(JSON, default=dict, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    
    __table_args__ = (
        Index("idx_session_user_status", "user_id", "status"),
        Index("idx_session_token", "session_token"),
        Index("idx_session_expires", "expires_at"),
        Index("idx_session_last_activity", "last_activity"),
        Index("idx_session_ip", "ip_address"),
        Index("idx_session_suspicious", "is_suspicious", "risk_score"),
    )
    
    @property
    def is_active(self) -> bool:
        """Check if session is currently active"""
        now = datetime.utcnow()
        return (
            self.status == SessionStatus.ACTIVE and
            self.expires_at > now and
            self.terminated_at is None
        )
    
    @property
    def is_expired(self) -> bool:
        """Check if session has expired"""
        now = datetime.utcnow()
        return self.expires_at <= now or self.status == SessionStatus.EXPIRED
    
    def __repr__(self):
        return f"<UserSession(user_id='{self.user_id}', status='{self.status}', ip='{self.ip_address}')>"


class SessionActivity(Base):
    """
    Detailed session activity tracking
    """
    __tablename__ = "session_activities"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("user_sessions.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Activity details
    activity_type = Column(String(50), nullable=False)  # login, logout, access, action
    activity_detail = Column(String(200), nullable=True)
    resource_accessed = Column(String(100), nullable=True)
    action_performed = Column(String(50), nullable=True)
    
    # Request details
    ip_address = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)
    request_method = Column(String(10), nullable=True)
    request_path = Column(String(500), nullable=True)
    response_status = Column(Integer, nullable=True)
    
    # Timing
    timestamp = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    duration_ms = Column(Integer, nullable=True)
    
    # Security
    risk_score = Column(Integer, default=0, nullable=False)
    anomaly_detected = Column(Boolean, default=False, nullable=False)
    
    # Additional data
    metadata = Column(JSON, default=dict, nullable=False)
    
    # Relationships
    session = relationship("UserSession")
    user = relationship("User")
    
    __table_args__ = (
        Index("idx_activity_session", "session_id", "timestamp"),
        Index("idx_activity_user", "user_id", "timestamp"),
        Index("idx_activity_type", "activity_type"),
        Index("idx_activity_timestamp", "timestamp"),
        Index("idx_activity_anomaly", "anomaly_detected", "risk_score"),
    )
    
    def __repr__(self):
        return f"<SessionActivity(session_id='{self.session_id}', type='{self.activity_type}', timestamp='{self.timestamp}')>"


class DeviceInfo(Base):
    """
    Device information for device-based security
    """
    __tablename__ = "device_info"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    device_fingerprint = Column(String(255), unique=True, nullable=False, index=True)
    
    # Device details
    device_name = Column(String(100), nullable=True)
    device_type = Column(String(50), nullable=True)  # desktop, mobile, tablet
    operating_system = Column(String(100), nullable=True)
    browser = Column(String(100), nullable=True)
    
    # Trust level
    is_trusted = Column(Boolean, default=False, nullable=False)
    trust_score = Column(Integer, default=0, nullable=False)  # 0-100
    
    # Usage tracking
    first_seen = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    last_seen = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    login_count = Column(Integer, default=0, nullable=False)
    
    # Geographic consistency
    usual_locations = Column(JSON, default=list, nullable=False)
    
    # Security flags
    is_blocked = Column(Boolean, default=False, nullable=False)
    blocked_reason = Column(String(200), nullable=True)
    blocked_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User")
    
    __table_args__ = (
        Index("idx_device_user", "user_id"),
        Index("idx_device_fingerprint", "device_fingerprint"),
        Index("idx_device_trusted", "is_trusted", "trust_score"),
        Index("idx_device_last_seen", "last_seen"),
    )
    
    def __repr__(self):
        return f"<DeviceInfo(user_id='{self.user_id}', fingerprint='{self.device_fingerprint[:16]}...', trusted='{self.is_trusted}')>"