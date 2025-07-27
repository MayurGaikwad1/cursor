"""
User models for authentication and user management
"""

import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    Boolean, Column, DateTime, String, Text, Integer, 
    ForeignKey, JSON, Enum as SQLEnum, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.database import Base


class UserStatus(str, enum.Enum):
    """User account status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    LOCKED = "locked"
    PENDING_ACTIVATION = "pending_activation"
    EXPIRED = "expired"


class User(Base):
    """
    User model for authentication and basic user information
    """
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(320), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    status = Column(SQLEnum(UserStatus), default=UserStatus.PENDING_ACTIVATION, nullable=False)
    
    # Account management
    is_superuser = Column(Boolean, default=False, nullable=False)
    is_staff = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    email_verified = Column(Boolean, default=False, nullable=False)
    phone_verified = Column(Boolean, default=False, nullable=False)
    
    # Security fields
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    password_changed_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    account_locked_until = Column(DateTime(timezone=True), nullable=True)
    force_password_change = Column(Boolean, default=False, nullable=False)
    
    # MFA settings
    mfa_enabled = Column(Boolean, default=False, nullable=False)
    backup_codes_used = Column(JSON, default=list, nullable=False)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Organization
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True)
    manager_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Relationships
    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    password_history = relationship("PasswordHistory", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    mfa_devices = relationship("MFADevice", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", foreign_keys="AuditLog.user_id", back_populates="user")
    
    # Organization relationships
    organization = relationship("Organization", back_populates="users")
    department = relationship("Department", back_populates="users")
    manager = relationship("User", remote_side=[id], backref="direct_reports")
    
    # Role relationships
    user_roles = relationship("UserRole", back_populates="user", cascade="all, delete-orphan")
    
    # Self-referential relationships for audit
    created_by_user = relationship("User", foreign_keys=[created_by], remote_side=[id])
    updated_by_user = relationship("User", foreign_keys=[updated_by], remote_side=[id])
    
    __table_args__ = (
        Index("idx_user_email_status", "email", "status"),
        Index("idx_user_username_status", "username", "status"),
        Index("idx_user_last_login", "last_login"),
        Index("idx_user_organization", "organization_id"),
        Index("idx_user_department", "department_id"),
    )
    
    def __repr__(self):
        return f"<User(username='{self.username}', email='{self.email}', status='{self.status}')>"


class UserProfile(Base):
    """
    Extended user profile information
    """
    __tablename__ = "user_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)
    
    # Personal information
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    middle_name = Column(String(100), nullable=True)
    display_name = Column(String(200), nullable=True)
    title = Column(String(100), nullable=True)
    
    # Contact information
    phone_number = Column(String(20), nullable=True)
    mobile_number = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    
    # Employment information
    employee_id = Column(String(50), nullable=True, unique=True)
    job_title = Column(String(200), nullable=True)
    hire_date = Column(DateTime(timezone=True), nullable=True)
    termination_date = Column(DateTime(timezone=True), nullable=True)
    employment_status = Column(String(50), nullable=True)
    
    # Additional information
    timezone = Column(String(50), default="UTC", nullable=False)
    locale = Column(String(10), default="en-US", nullable=False)
    avatar_url = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    
    # Preferences
    preferences = Column(JSON, default=dict, nullable=False)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="profile")
    
    __table_args__ = (
        Index("idx_profile_employee_id", "employee_id"),
        Index("idx_profile_name", "first_name", "last_name"),
    )
    
    @property
    def full_name(self) -> str:
        """Get full name"""
        names = [self.first_name, self.middle_name, self.last_name]
        return " ".join(name for name in names if name)
    
    def __repr__(self):
        return f"<UserProfile(user_id='{self.user_id}', name='{self.full_name}')>"


class PasswordHistory(Base):
    """
    Password history for policy enforcement
    """
    __tablename__ = "password_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="password_history")
    
    __table_args__ = (
        Index("idx_password_history_user", "user_id", "created_at"),
    )
    
    def __repr__(self):
        return f"<PasswordHistory(user_id='{self.user_id}', created_at='{self.created_at}')>"


class UserRole(Base):
    """
    User-Role association table with additional metadata
    """
    __tablename__ = "user_roles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"), nullable=False)
    
    # Assignment metadata
    assigned_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    assigned_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="user_roles")
    role = relationship("Role", back_populates="user_roles")
    assigned_by_user = relationship("User", foreign_keys=[assigned_by])
    
    __table_args__ = (
        UniqueConstraint("user_id", "role_id", name="uq_user_role"),
        Index("idx_user_role_active", "user_id", "role_id", "is_active"),
        Index("idx_user_role_expires", "expires_at"),
    )
    
    def __repr__(self):
        return f"<UserRole(user_id='{self.user_id}', role_id='{self.role_id}', active='{self.is_active}')>"