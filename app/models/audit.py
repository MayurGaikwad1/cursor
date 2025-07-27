"""
Audit logging models for compliance and security
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


class AuditEventType(str, enum.Enum):
    """Audit event types"""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    USER_MANAGEMENT = "user_management"
    ROLE_MANAGEMENT = "role_management"
    PERMISSION_MANAGEMENT = "permission_management"
    SESSION_MANAGEMENT = "session_management"
    DATA_ACCESS = "data_access"
    CONFIGURATION_CHANGE = "configuration_change"
    SECURITY_EVENT = "security_event"
    COMPLIANCE_EVENT = "compliance_event"
    SYSTEM_EVENT = "system_event"


class AuditSeverity(str, enum.Enum):
    """Audit event severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditOutcome(str, enum.Enum):
    """Audit event outcomes"""
    SUCCESS = "success"
    FAILURE = "failure"
    UNKNOWN = "unknown"


class AuditLog(Base):
    """
    Comprehensive audit logging model
    """
    __tablename__ = "audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Event identification
    event_type = Column(SQLEnum(AuditEventType), nullable=False, index=True)
    event_category = Column(String(100), nullable=False)  # More specific categorization
    event_action = Column(String(100), nullable=False)    # Specific action taken
    event_outcome = Column(SQLEnum(AuditOutcome), default=AuditOutcome.SUCCESS, nullable=False)
    severity = Column(SQLEnum(AuditSeverity), default=AuditSeverity.INFO, nullable=False)
    
    # Actor information
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("user_sessions.id"), nullable=True)
    acting_as_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)  # For impersonation
    
    # Target information
    target_type = Column(String(100), nullable=True)      # Type of resource affected
    target_id = Column(String(255), nullable=True)        # ID of affected resource
    target_details = Column(JSON, default=dict, nullable=False)  # Additional target info
    
    # Request context
    ip_address = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)
    request_method = Column(String(10), nullable=True)
    request_path = Column(String(500), nullable=True)
    request_id = Column(String(100), nullable=True)       # Correlation ID
    
    # Event details
    message = Column(Text, nullable=False)                 # Human-readable description
    details = Column(JSON, default=dict, nullable=False)  # Structured event data
    changes = Column(JSON, default=dict, nullable=False)  # Before/after values
    
    # Security context
    risk_score = Column(Integer, default=0, nullable=False)  # 0-100
    compliance_tags = Column(JSON, default=list, nullable=False)  # Compliance frameworks
    
    # Timing
    timestamp = Column(DateTime(timezone=True), default=func.now(), nullable=False, index=True)
    duration_ms = Column(Integer, nullable=True)
    
    # System context
    source_system = Column(String(100), nullable=True)
    source_component = Column(String(100), nullable=True)
    environment = Column(String(50), nullable=True)       # dev, staging, prod
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="audit_logs")
    acting_as_user = relationship("User", foreign_keys=[acting_as_user_id])
    session = relationship("UserSession")
    
    __table_args__ = (
        Index("idx_audit_timestamp", "timestamp"),
        Index("idx_audit_user", "user_id", "timestamp"),
        Index("idx_audit_event_type", "event_type", "timestamp"),
        Index("idx_audit_severity", "severity", "timestamp"),
        Index("idx_audit_outcome", "event_outcome", "timestamp"),
        Index("idx_audit_target", "target_type", "target_id"),
        Index("idx_audit_ip", "ip_address"),
        Index("idx_audit_session", "session_id"),
        Index("idx_audit_risk", "risk_score"),
        Index("idx_audit_compliance", "compliance_tags"),
    )
    
    def __repr__(self):
        return f"<AuditLog(event_type='{self.event_type}', action='{self.event_action}', user_id='{self.user_id}', timestamp='{self.timestamp}')>"


class ComplianceReport(Base):
    """
    Compliance reporting and tracking
    """
    __tablename__ = "compliance_reports"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Report identification
    report_type = Column(String(100), nullable=False)     # SOX, GDPR, HIPAA, etc.
    report_name = Column(String(200), nullable=False)
    report_period_start = Column(DateTime(timezone=True), nullable=False)
    report_period_end = Column(DateTime(timezone=True), nullable=False)
    
    # Report status
    status = Column(String(50), default="draft", nullable=False)  # draft, final, submitted
    generated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Report content
    summary = Column(JSON, default=dict, nullable=False)
    findings = Column(JSON, default=list, nullable=False)
    recommendations = Column(JSON, default=list, nullable=False)
    
    # Metrics
    total_events = Column(Integer, default=0, nullable=False)
    security_events = Column(Integer, default=0, nullable=False)
    policy_violations = Column(Integer, default=0, nullable=False)
    
    # File references
    report_file_path = Column(String(500), nullable=True)
    report_file_hash = Column(String(64), nullable=True)   # SHA-256
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    generated_by_user = relationship("User", foreign_keys=[generated_by])
    approved_by_user = relationship("User", foreign_keys=[approved_by])
    
    __table_args__ = (
        Index("idx_compliance_type", "report_type"),
        Index("idx_compliance_period", "report_period_start", "report_period_end"),
        Index("idx_compliance_status", "status"),
        Index("idx_compliance_created", "created_at"),
    )
    
    def __repr__(self):
        return f"<ComplianceReport(type='{self.report_type}', name='{self.report_name}', status='{self.status}')>"


class DataRetention(Base):
    """
    Data retention policy enforcement tracking
    """
    __tablename__ = "data_retention"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Policy information
    policy_name = Column(String(200), nullable=False)
    data_type = Column(String(100), nullable=False)       # audit_logs, user_data, etc.
    retention_period_days = Column(Integer, nullable=False)
    
    # Data identification
    data_table = Column(String(100), nullable=False)
    data_id = Column(String(255), nullable=True)
    data_created_at = Column(DateTime(timezone=True), nullable=False)
    data_eligible_for_deletion_at = Column(DateTime(timezone=True), nullable=False)
    
    # Processing status
    status = Column(String(50), default="pending", nullable=False)  # pending, archived, deleted, exempt
    processed_at = Column(DateTime(timezone=True), nullable=True)
    processed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Legal hold
    legal_hold = Column(Boolean, default=False, nullable=False)
    legal_hold_reason = Column(Text, nullable=True)
    legal_hold_until = Column(DateTime(timezone=True), nullable=True)
    
    # Additional metadata
    metadata = Column(JSON, default=dict, nullable=False)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    processed_by_user = relationship("User", foreign_keys=[processed_by])
    
    __table_args__ = (
        Index("idx_retention_eligible", "data_eligible_for_deletion_at"),
        Index("idx_retention_status", "status"),
        Index("idx_retention_data", "data_table", "data_id"),
        Index("idx_retention_legal_hold", "legal_hold"),
        Index("idx_retention_policy", "policy_name"),
    )
    
    def __repr__(self):
        return f"<DataRetention(policy='{self.policy_name}', data_type='{self.data_type}', status='{self.status}')>"