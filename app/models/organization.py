"""
Organization and department models
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Boolean, Column, DateTime, String, Text, Integer, 
    ForeignKey, JSON, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Organization(Base):
    """
    Organization model for multi-tenancy
    """
    __tablename__ = "organizations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Basic information
    name = Column(String(200), nullable=False, index=True)
    display_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    code = Column(String(50), unique=True, nullable=False, index=True)  # Short identifier
    
    # Contact information
    website = Column(String(255), nullable=True)
    email = Column(String(320), nullable=True)
    phone = Column(String(20), nullable=True)
    
    # Address information
    address_line1 = Column(String(255), nullable=True)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    
    # Organization settings
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Hierarchy
    parent_organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)
    level = Column(Integer, default=0, nullable=False)
    
    # Configuration
    settings = Column(JSON, default=dict, nullable=False)
    
    # License and compliance
    license_type = Column(String(50), nullable=True)        # free, standard, enterprise
    max_users = Column(Integer, nullable=True)
    compliance_frameworks = Column(JSON, default=list, nullable=False)  # SOX, GDPR, etc.
    
    # Branding
    logo_url = Column(String(500), nullable=True)
    theme_config = Column(JSON, default=dict, nullable=False)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Relationships
    parent_organization = relationship("Organization", remote_side=[id], backref="child_organizations")
    users = relationship("User", back_populates="organization")
    departments = relationship("Department", back_populates="organization", cascade="all, delete-orphan")
    roles = relationship("Role", back_populates="organization")
    
    # Audit relationships
    created_by_user = relationship("User", foreign_keys=[created_by])
    updated_by_user = relationship("User", foreign_keys=[updated_by])
    
    __table_args__ = (
        Index("idx_org_name", "name"),
        Index("idx_org_code", "code"),
        Index("idx_org_active", "is_active"),
        Index("idx_org_parent", "parent_organization_id"),
        Index("idx_org_level", "level"),
    )
    
    def __repr__(self):
        return f"<Organization(name='{self.name}', code='{self.code}', active='{self.is_active}')>"


class Department(Base):
    """
    Department model for organizational structure
    """
    __tablename__ = "departments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    
    # Basic information
    name = Column(String(200), nullable=False)
    display_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    code = Column(String(50), nullable=False)  # Unique within organization
    
    # Hierarchy
    parent_department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True)
    level = Column(Integer, default=0, nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Management
    manager_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    cost_center = Column(String(50), nullable=True)
    budget_code = Column(String(50), nullable=True)
    
    # Contact information
    email = Column(String(320), nullable=True)
    phone = Column(String(20), nullable=True)
    location = Column(String(200), nullable=True)
    
    # Configuration
    settings = Column(JSON, default=dict, nullable=False)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Relationships
    organization = relationship("Organization", back_populates="departments")
    parent_department = relationship("Department", remote_side=[id], backref="child_departments")
    users = relationship("User", back_populates="department")
    roles = relationship("Role", back_populates="department")
    manager = relationship("User", foreign_keys=[manager_id])
    
    # Audit relationships
    created_by_user = relationship("User", foreign_keys=[created_by])
    updated_by_user = relationship("User", foreign_keys=[updated_by])
    
    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_org_dept_code"),
        Index("idx_dept_organization", "organization_id"),
        Index("idx_dept_name", "name"),
        Index("idx_dept_code", "code"),
        Index("idx_dept_active", "is_active"),
        Index("idx_dept_parent", "parent_department_id"),
        Index("idx_dept_manager", "manager_id"),
    )
    
    def __repr__(self):
        return f"<Department(name='{self.name}', code='{self.code}', org_id='{self.organization_id}')>"


class OrganizationSettings(Base):
    """
    Organization-specific security and policy settings
    """
    __tablename__ = "organization_settings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, unique=True)
    
    # Authentication settings
    enforce_mfa = Column(Boolean, default=False, nullable=False)
    mfa_grace_period_days = Column(Integer, default=7, nullable=False)
    allowed_login_methods = Column(JSON, default=list, nullable=False)
    
    # Password policy
    password_min_length = Column(Integer, default=12, nullable=False)
    password_require_uppercase = Column(Boolean, default=True, nullable=False)
    password_require_lowercase = Column(Boolean, default=True, nullable=False)
    password_require_numbers = Column(Boolean, default=True, nullable=False)
    password_require_special = Column(Boolean, default=True, nullable=False)
    password_history_count = Column(Integer, default=12, nullable=False)
    password_expiry_days = Column(Integer, default=90, nullable=False)
    
    # Session settings
    session_timeout_minutes = Column(Integer, default=480, nullable=False)
    max_concurrent_sessions = Column(Integer, default=5, nullable=False)
    idle_timeout_minutes = Column(Integer, default=30, nullable=False)
    
    # Account lockout
    max_failed_attempts = Column(Integer, default=5, nullable=False)
    lockout_duration_minutes = Column(Integer, default=15, nullable=False)
    auto_unlock = Column(Boolean, default=True, nullable=False)
    
    # IP restrictions
    ip_whitelist = Column(JSON, default=list, nullable=False)
    ip_blacklist = Column(JSON, default=list, nullable=False)
    geo_restrictions = Column(JSON, default=dict, nullable=False)
    
    # Audit settings
    audit_retention_days = Column(Integer, default=2555, nullable=False)  # 7 years
    audit_log_level = Column(String(20), default="INFO", nullable=False)
    
    # Compliance settings
    gdpr_enabled = Column(Boolean, default=False, nullable=False)
    data_residency_region = Column(String(100), nullable=True)
    encryption_at_rest = Column(Boolean, default=True, nullable=False)
    
    # Notification settings
    security_notifications = Column(Boolean, default=True, nullable=False)
    admin_email_notifications = Column(Boolean, default=True, nullable=False)
    user_email_notifications = Column(Boolean, default=True, nullable=False)
    
    # API settings
    api_rate_limit_per_minute = Column(Integer, default=1000, nullable=False)
    api_key_expiry_days = Column(Integer, default=365, nullable=False)
    
    # Integration settings
    ldap_enabled = Column(Boolean, default=False, nullable=False)
    sso_enabled = Column(Boolean, default=False, nullable=False)
    saml_enabled = Column(Boolean, default=False, nullable=False)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Relationships
    organization = relationship("Organization")
    updated_by_user = relationship("User", foreign_keys=[updated_by])
    
    __table_args__ = (
        Index("idx_org_settings_org", "organization_id"),
    )
    
    def __repr__(self):
        return f"<OrganizationSettings(org_id='{self.organization_id}', mfa_enforced='{self.enforce_mfa}')>"