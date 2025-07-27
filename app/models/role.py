"""
Role-based access control models
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


class RoleType(str, enum.Enum):
    """Role types"""
    SYSTEM = "system"
    BUSINESS = "business"
    FUNCTIONAL = "functional"
    TEMPORARY = "temporary"


class PermissionType(str, enum.Enum):
    """Permission types"""
    RESOURCE = "resource"
    ACTION = "action"
    DATA = "data"
    SYSTEM = "system"


class Role(Base):
    """
    Role model for RBAC implementation
    """
    __tablename__ = "roles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    role_type = Column(SQLEnum(RoleType), default=RoleType.BUSINESS, nullable=False)
    
    # Role hierarchy
    parent_role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"), nullable=True)
    level = Column(Integer, default=0, nullable=False)
    
    # Status and lifecycle
    is_active = Column(Boolean, default=True, nullable=False)
    is_system_role = Column(Boolean, default=False, nullable=False)
    is_assignable = Column(Boolean, default=True, nullable=False)
    
    # Metadata
    tags = Column(JSON, default=list, nullable=False)
    metadata = Column(JSON, default=dict, nullable=False)
    
    # Organization context
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id"), nullable=True)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Relationships
    parent_role = relationship("Role", remote_side=[id], backref="child_roles")
    role_permissions = relationship("RolePermission", back_populates="role", cascade="all, delete-orphan")
    user_roles = relationship("UserRole", back_populates="role", cascade="all, delete-orphan")
    
    # Organization relationships
    organization = relationship("Organization", back_populates="roles")
    department = relationship("Department", back_populates="roles")
    
    # Audit relationships
    created_by_user = relationship("User", foreign_keys=[created_by])
    updated_by_user = relationship("User", foreign_keys=[updated_by])
    
    __table_args__ = (
        Index("idx_role_name_active", "name", "is_active"),
        Index("idx_role_type", "role_type"),
        Index("idx_role_organization", "organization_id"),
        Index("idx_role_department", "department_id"),
        Index("idx_role_hierarchy", "parent_role_id", "level"),
    )
    
    def __repr__(self):
        return f"<Role(name='{self.name}', type='{self.role_type}', active='{self.is_active}')>"


class Permission(Base):
    """
    Permission model for fine-grained access control
    """
    __tablename__ = "permissions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    permission_type = Column(SQLEnum(PermissionType), default=PermissionType.RESOURCE, nullable=False)
    
    # Permission details
    resource = Column(String(100), nullable=False)  # e.g., 'user', 'role', 'report'
    action = Column(String(50), nullable=False)     # e.g., 'create', 'read', 'update', 'delete'
    scope = Column(String(100), nullable=True)      # e.g., 'own', 'department', 'organization', 'all'
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_system_permission = Column(Boolean, default=False, nullable=False)
    
    # Metadata
    tags = Column(JSON, default=list, nullable=False)
    conditions = Column(JSON, default=dict, nullable=False)  # ABAC conditions
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Relationships
    role_permissions = relationship("RolePermission", back_populates="permission", cascade="all, delete-orphan")
    
    # Audit relationships
    created_by_user = relationship("User", foreign_keys=[created_by])
    updated_by_user = relationship("User", foreign_keys=[updated_by])
    
    __table_args__ = (
        Index("idx_permission_resource_action", "resource", "action"),
        Index("idx_permission_type", "permission_type"),
        Index("idx_permission_active", "is_active"),
        UniqueConstraint("resource", "action", "scope", name="uq_permission_ras"),
    )
    
    @property
    def full_name(self) -> str:
        """Get full permission name in format resource:action:scope"""
        parts = [self.resource, self.action]
        if self.scope:
            parts.append(self.scope)
        return ":".join(parts)
    
    def __repr__(self):
        return f"<Permission(name='{self.name}', resource='{self.resource}', action='{self.action}')>"


class RolePermission(Base):
    """
    Role-Permission association table with conditions
    """
    __tablename__ = "role_permissions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"), nullable=False)
    permission_id = Column(UUID(as_uuid=True), ForeignKey("permissions.id"), nullable=False)
    
    # Permission grant details
    granted_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    granted_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # ABAC conditions specific to this role-permission assignment
    conditions = Column(JSON, default=dict, nullable=False)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    role = relationship("Role", back_populates="role_permissions")
    permission = relationship("Permission", back_populates="role_permissions")
    granted_by_user = relationship("User", foreign_keys=[granted_by])
    
    __table_args__ = (
        UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),
        Index("idx_role_permission_active", "role_id", "permission_id", "is_active"),
        Index("idx_role_permission_expires", "expires_at"),
    )
    
    def __repr__(self):
        return f"<RolePermission(role_id='{self.role_id}', permission_id='{self.permission_id}', active='{self.is_active}')>"


class RoleHierarchy(Base):
    """
    Role hierarchy for inheritance of permissions
    """
    __tablename__ = "role_hierarchy"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parent_role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"), nullable=False)
    child_role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"), nullable=False)
    depth = Column(Integer, default=1, nullable=False)  # Distance in hierarchy
    
    # Inheritance rules
    inherit_permissions = Column(Boolean, default=True, nullable=False)
    inherit_conditions = Column(Boolean, default=False, nullable=False)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Relationships
    parent_role = relationship("Role", foreign_keys=[parent_role_id])
    child_role = relationship("Role", foreign_keys=[child_role_id])
    created_by_user = relationship("User", foreign_keys=[created_by])
    
    __table_args__ = (
        UniqueConstraint("parent_role_id", "child_role_id", name="uq_role_hierarchy"),
        Index("idx_role_hierarchy_parent", "parent_role_id"),
        Index("idx_role_hierarchy_child", "child_role_id"),
        Index("idx_role_hierarchy_depth", "depth"),
    )
    
    def __repr__(self):
        return f"<RoleHierarchy(parent='{self.parent_role_id}', child='{self.child_role_id}', depth={self.depth})>"