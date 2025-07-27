"""
Notification and communication models
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Boolean, Column, DateTime, String, Text, Integer, 
    ForeignKey, JSON, Enum as SQLEnum, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.database import Base


class NotificationType(str, enum.Enum):
    """Notification types"""
    SECURITY_ALERT = "security_alert"
    ACCESS_REQUEST = "access_request"
    PASSWORD_EXPIRY = "password_expiry"
    MFA_SETUP = "mfa_setup"
    LOGIN_ALERT = "login_alert"
    COMPLIANCE_VIOLATION = "compliance_violation"
    SYSTEM_MAINTENANCE = "system_maintenance"
    WELCOME = "welcome"
    ACCOUNT_LOCKED = "account_locked"
    ROLE_ASSIGNMENT = "role_assignment"


class NotificationChannel(str, enum.Enum):
    """Notification delivery channels"""
    EMAIL = "email"
    SMS = "sms"
    IN_APP = "in_app"
    PUSH = "push"
    SLACK = "slack"
    WEBHOOK = "webhook"


class NotificationPriority(str, enum.Enum):
    """Notification priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationStatus(str, enum.Enum):
    """Notification delivery status"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    CANCELLED = "cancelled"


class NotificationTemplate(Base):
    """
    Notification template for different types of communications
    """
    __tablename__ = "notification_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Template identification
    name = Column(String(200), nullable=False, index=True)
    notification_type = Column(SQLEnum(NotificationType), nullable=False)
    channel = Column(SQLEnum(NotificationChannel), nullable=False)
    
    # Template content
    subject_template = Column(String(500), nullable=True)
    body_template = Column(Text, nullable=False)
    html_template = Column(Text, nullable=True)
    
    # Template metadata
    language = Column(String(10), default="en", nullable=False)
    version = Column(String(20), default="1.0", nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)
    
    # Organization context
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)
    
    # Template variables and settings
    variables = Column(JSON, default=list, nullable=False)  # Available template variables
    settings = Column(JSON, default=dict, nullable=False)   # Channel-specific settings
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Relationships
    organization = relationship("Organization")
    notification_logs = relationship("NotificationLog", back_populates="template")
    
    # Audit relationships
    created_by_user = relationship("User", foreign_keys=[created_by])
    updated_by_user = relationship("User", foreign_keys=[updated_by])
    
    __table_args__ = (
        Index("idx_notification_template_type", "notification_type"),
        Index("idx_notification_template_channel", "channel"),
        Index("idx_notification_template_active", "is_active"),
        Index("idx_notification_template_org", "organization_id"),
    )
    
    def __repr__(self):
        return f"<NotificationTemplate(name='{self.name}', type='{self.notification_type}', channel='{self.channel}')>"


class NotificationLog(Base):
    """
    Log of all notifications sent
    """
    __tablename__ = "notification_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Notification identification
    notification_type = Column(SQLEnum(NotificationType), nullable=False)
    channel = Column(SQLEnum(NotificationChannel), nullable=False)
    priority = Column(SQLEnum(NotificationPriority), default=NotificationPriority.NORMAL, nullable=False)
    
    # Recipient information
    recipient_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    recipient_email = Column(String(320), nullable=True)
    recipient_phone = Column(String(20), nullable=True)
    recipient_address = Column(String(500), nullable=True)  # Generic recipient address
    
    # Message content
    subject = Column(String(500), nullable=True)
    message = Column(Text, nullable=False)
    html_content = Column(Text, nullable=True)
    
    # Template reference
    template_id = Column(UUID(as_uuid=True), ForeignKey("notification_templates.id"), nullable=True)
    template_variables = Column(JSON, default=dict, nullable=False)
    
    # Delivery status
    status = Column(SQLEnum(NotificationStatus), default=NotificationStatus.PENDING, nullable=False)
    attempts = Column(Integer, default=0, nullable=False)
    max_attempts = Column(Integer, default=3, nullable=False)
    
    # Timing
    scheduled_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    failed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Delivery details
    provider = Column(String(100), nullable=True)          # Email/SMS provider used
    provider_message_id = Column(String(255), nullable=True)  # Provider's message ID
    delivery_response = Column(JSON, default=dict, nullable=False)  # Provider response
    
    # Error handling
    error_message = Column(Text, nullable=True)
    retry_after = Column(DateTime(timezone=True), nullable=True)
    
    # Context information
    triggered_by_event = Column(String(100), nullable=True)
    event_id = Column(String(255), nullable=True)
    user_session_id = Column(UUID(as_uuid=True), ForeignKey("user_sessions.id"), nullable=True)
    
    # Organization context
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)
    
    # Additional metadata
    metadata = Column(JSON, default=dict, nullable=False)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    recipient = relationship("User", foreign_keys=[recipient_id])
    template = relationship("NotificationTemplate", back_populates="notification_logs")
    user_session = relationship("UserSession")
    organization = relationship("Organization")
    
    __table_args__ = (
        Index("idx_notification_log_type", "notification_type"),
        Index("idx_notification_log_channel", "channel"),
        Index("idx_notification_log_recipient", "recipient_id"),
        Index("idx_notification_log_status", "status"),
        Index("idx_notification_log_scheduled", "scheduled_at"),
        Index("idx_notification_log_priority", "priority"),
        Index("idx_notification_log_organization", "organization_id"),
        Index("idx_notification_log_event", "triggered_by_event", "event_id"),
    )
    
    def __repr__(self):
        return f"<NotificationLog(type='{self.notification_type}', channel='{self.channel}', status='{self.status}', recipient_id='{self.recipient_id}')>"


class NotificationPreferences(Base):
    """
    User notification preferences
    """
    __tablename__ = "notification_preferences"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)
    
    # Email preferences
    email_enabled = Column(Boolean, default=True, nullable=False)
    email_security_alerts = Column(Boolean, default=True, nullable=False)
    email_access_requests = Column(Boolean, default=True, nullable=False)
    email_password_expiry = Column(Boolean, default=True, nullable=False)
    email_login_alerts = Column(Boolean, default=False, nullable=False)
    email_compliance = Column(Boolean, default=True, nullable=False)
    email_system_maintenance = Column(Boolean, default=True, nullable=False)
    
    # SMS preferences
    sms_enabled = Column(Boolean, default=False, nullable=False)
    sms_security_alerts = Column(Boolean, default=True, nullable=False)
    sms_access_requests = Column(Boolean, default=False, nullable=False)
    sms_login_alerts = Column(Boolean, default=False, nullable=False)
    sms_mfa_codes = Column(Boolean, default=True, nullable=False)
    
    # In-app preferences
    in_app_enabled = Column(Boolean, default=True, nullable=False)
    in_app_security_alerts = Column(Boolean, default=True, nullable=False)
    in_app_access_requests = Column(Boolean, default=True, nullable=False)
    in_app_system_messages = Column(Boolean, default=True, nullable=False)
    
    # Push notification preferences
    push_enabled = Column(Boolean, default=False, nullable=False)
    push_security_alerts = Column(Boolean, default=True, nullable=False)
    push_login_alerts = Column(Boolean, default=False, nullable=False)
    
    # Frequency settings
    digest_frequency = Column(String(20), default="daily", nullable=False)  # none, daily, weekly
    quiet_hours_start = Column(String(5), nullable=True)  # HH:MM format
    quiet_hours_end = Column(String(5), nullable=True)    # HH:MM format
    timezone = Column(String(50), default="UTC", nullable=False)
    
    # Language and formatting
    language = Column(String(10), default="en", nullable=False)
    date_format = Column(String(20), default="YYYY-MM-DD", nullable=False)
    time_format = Column(String(10), default="24h", nullable=False)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User")
    
    __table_args__ = (
        Index("idx_notification_prefs_user", "user_id"),
    )
    
    def __repr__(self):
        return f"<NotificationPreferences(user_id='{self.user_id}', email_enabled='{self.email_enabled}', sms_enabled='{self.sms_enabled}')>"