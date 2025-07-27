"""
Policy and access management models
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


class PolicyType(str, enum.Enum):
    """Policy types"""
    ACCESS = "access"
    SECURITY = "security"
    COMPLIANCE = "compliance"
    DATA = "data"
    WORKFLOW = "workflow"


class PolicyStatus(str, enum.Enum):
    """Policy status"""
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"


class AccessRequestStatus(str, enum.Enum):
    """Access request status"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    REVOKED = "revoked"


class Policy(Base):
    """
    Policy model for access control and compliance
    """
    __tablename__ = "policies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Basic information
    name = Column(String(200), nullable=False, index=True)
    display_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    policy_type = Column(SQLEnum(PolicyType), nullable=False)
    
    # Status and lifecycle
    status = Column(SQLEnum(PolicyStatus), default=PolicyStatus.DRAFT, nullable=False)
    version = Column(String(20), default="1.0", nullable=False)
    effective_date = Column(DateTime(timezone=True), nullable=True)
    expiry_date = Column(DateTime(timezone=True), nullable=True)
    
    # Policy content
    rules = Column(JSON, default=list, nullable=False)  # List of policy rules
    conditions = Column(JSON, default=dict, nullable=False)  # ABAC conditions
    actions = Column(JSON, default=list, nullable=False)  # Actions to take
    
    # Priority and enforcement
    priority = Column(Integer, default=100, nullable=False)  # Lower = higher priority
    enforce_mode = Column(String(20), default="enforce", nullable=False)  # enforce, warn, log
    
    # Organization context
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True)
    
    # Compliance
    compliance_frameworks = Column(JSON, default=list, nullable=False)
    
    # Metadata
    tags = Column(JSON, default=list, nullable=False)
    metadata = Column(JSON, default=dict, nullable=False)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Relationships
    organization = relationship("Organization")
    department = relationship("Department")
    policy_rules = relationship("PolicyRule", back_populates="policy", cascade="all, delete-orphan")
    access_requests = relationship("AccessRequest", back_populates="policy")
    
    # Audit relationships
    created_by_user = relationship("User", foreign_keys=[created_by])
    updated_by_user = relationship("User", foreign_keys=[updated_by])
    
    __table_args__ = (
        Index("idx_policy_name", "name"),
        Index("idx_policy_type", "policy_type"),
        Index("idx_policy_status", "status"),
        Index("idx_policy_organization", "organization_id"),
        Index("idx_policy_priority", "priority"),
        Index("idx_policy_effective", "effective_date", "expiry_date"),
        UniqueConstraint("name", "version", name="uq_policy_name_version"),
    )
    
    def __repr__(self):
        return f"<Policy(name='{self.name}', type='{self.policy_type}', status='{self.status}')>"


class PolicyRule(Base):
    """
    Individual policy rules within a policy
    """
    __tablename__ = "policy_rules"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    policy_id = Column(UUID(as_uuid=True), ForeignKey("policies.id"), nullable=False)
    
    # Rule identification
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    rule_order = Column(Integer, default=0, nullable=False)
    
    # Rule definition
    condition = Column(JSON, nullable=False)  # ABAC condition expression
    action = Column(String(50), nullable=False)  # allow, deny, require_approval
    effect = Column(String(50), default="allow", nullable=False)
    
    # Rule configuration
    is_active = Column(Boolean, default=True, nullable=False)
    is_mandatory = Column(Boolean, default=False, nullable=False)
    
    # Additional settings
    settings = Column(JSON, default=dict, nullable=False)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    policy = relationship("Policy", back_populates="policy_rules")
    
    __table_args__ = (
        Index("idx_policy_rule_policy", "policy_id", "rule_order"),
        Index("idx_policy_rule_active", "is_active"),
        UniqueConstraint("policy_id", "name", name="uq_policy_rule_name"),
    )
    
    def __repr__(self):
        return f"<PolicyRule(policy_id='{self.policy_id}', name='{self.name}', action='{self.action}')>"


class AccessRequest(Base):
    """
    Access request tracking and approval workflow
    """
    __tablename__ = "access_requests"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Request identification
    request_number = Column(String(50), unique=True, nullable=False, index=True)
    
    # Requester information
    requester_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    requested_for_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)  # If requesting for someone else
    
    # Request details
    request_type = Column(String(50), nullable=False)  # role_assignment, permission_grant, resource_access
    resource_type = Column(String(100), nullable=True)
    resource_id = Column(String(255), nullable=True)
    
    # What's being requested
    requested_roles = Column(JSON, default=list, nullable=False)
    requested_permissions = Column(JSON, default=list, nullable=False)
    requested_access = Column(JSON, default=dict, nullable=False)
    
    # Justification and context
    business_justification = Column(Text, nullable=False)
    urgency = Column(String(20), default="normal", nullable=False)  # low, normal, high, critical
    duration_days = Column(Integer, nullable=True)  # For temporary access
    
    # Status and workflow
    status = Column(SQLEnum(AccessRequestStatus), default=AccessRequestStatus.PENDING, nullable=False)
    current_approver_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approval_workflow = Column(JSON, default=list, nullable=False)  # Workflow steps
    
    # Policy context
    policy_id = Column(UUID(as_uuid=True), ForeignKey("policies.id"), nullable=True)
    policy_evaluation = Column(JSON, default=dict, nullable=False)
    
    # Timing
    requested_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    required_by = Column(DateTime(timezone=True), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    rejected_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Decision details
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    rejected_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    decision_reason = Column(Text, nullable=True)
    
    # Implementation
    implemented = Column(Boolean, default=False, nullable=False)
    implemented_at = Column(DateTime(timezone=True), nullable=True)
    implemented_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Additional data
    metadata = Column(JSON, default=dict, nullable=False)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    requester = relationship("User", foreign_keys=[requester_id])
    requested_for = relationship("User", foreign_keys=[requested_for_id])
    current_approver = relationship("User", foreign_keys=[current_approver_id])
    approved_by_user = relationship("User", foreign_keys=[approved_by])
    rejected_by_user = relationship("User", foreign_keys=[rejected_by])
    implemented_by_user = relationship("User", foreign_keys=[implemented_by])
    policy = relationship("Policy", back_populates="access_requests")
    
    __table_args__ = (
        Index("idx_access_request_number", "request_number"),
        Index("idx_access_request_requester", "requester_id"),
        Index("idx_access_request_status", "status"),
        Index("idx_access_request_approver", "current_approver_id"),
        Index("idx_access_request_requested", "requested_at"),
        Index("idx_access_request_expires", "expires_at"),
        Index("idx_access_request_type", "request_type"),
    )
    
    def __repr__(self):
        return f"<AccessRequest(number='{self.request_number}', status='{self.status}', requester_id='{self.requester_id}')>"