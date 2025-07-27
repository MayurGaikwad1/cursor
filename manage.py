#!/usr/bin/env python3
"""
ELAMS Management Script
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.config import settings
from app.database import engine, Base, init_database, close_database


async def create_tables():
    """Create all database tables"""
    print("Creating database tables...")
    try:
        await init_database()
        print("✅ Database tables created successfully")
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        sys.exit(1)


async def drop_tables():
    """Drop all database tables"""
    print("Dropping database tables...")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        print("✅ Database tables dropped successfully")
    except Exception as e:
        print(f"❌ Error dropping tables: {e}")
        sys.exit(1)


async def reset_database():
    """Reset the database (drop and recreate tables)"""
    print("Resetting database...")
    await drop_tables()
    await create_tables()
    print("✅ Database reset completed")


async def create_admin():
    """Create an admin user"""
    from app.models.user import User, UserProfile, UserStatus
    from app.models.role import Role, RoleType
    from app.models.organization import Organization
    from app.core.security import get_password_hash
    from app.database import async_session_maker
    import uuid
    
    print("Creating admin user...")
    
    try:
        async with async_session_maker() as session:
            # Create default organization if it doesn't exist
            org = await session.get(Organization, uuid.UUID("00000000-0000-0000-0000-000000000001"))
            if not org:
                org = Organization(
                    id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                    name="ELAMS Administration",
                    display_name="ELAMS Administration",
                    code="ADMIN",
                    is_active=True,
                    is_verified=True
                )
                session.add(org)
            
            # Create superuser role if it doesn't exist
            superuser_role = await session.get(Role, uuid.UUID("00000000-0000-0000-0000-000000000002"))
            if not superuser_role:
                superuser_role = Role(
                    id=uuid.UUID("00000000-0000-0000-0000-000000000002"),
                    name="superuser",
                    display_name="Super User",
                    description="Full system access",
                    role_type=RoleType.SYSTEM,
                    is_system_role=True,
                    organization_id=org.id
                )
                session.add(superuser_role)
            
            # Check if admin user already exists
            from sqlalchemy import select
            result = await session.execute(
                select(User).where(User.username == "admin")
            )
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                print("❌ Admin user already exists")
                return
            
            # Create admin user
            admin_user = User(
                username="admin",
                email="admin@elams.local",
                password_hash=get_password_hash("Admin123!@#"),
                status=UserStatus.ACTIVE,
                is_superuser=True,
                is_staff=True,
                is_active=True,
                email_verified=True,
                organization_id=org.id
            )
            session.add(admin_user)
            
            # Create admin profile
            admin_profile = UserProfile(
                user_id=admin_user.id,
                first_name="System",
                last_name="Administrator",
                display_name="System Administrator",
                title="System Administrator",
                employee_id="ADMIN001"
            )
            session.add(admin_profile)
            
            await session.commit()
            
        print("✅ Admin user created successfully")
        print("   Username: admin")
        print("   Password: Admin123!@#")
        print("   Email: admin@elams.local")
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        sys.exit(1)


async def run_migrations():
    """Run database migrations"""
    print("Running database migrations...")
    # This would integrate with Alembic in a real implementation
    await create_tables()
    print("✅ Migrations completed")


def print_help():
    """Print help information"""
    print("""
ELAMS Management Script

Usage: python manage.py <command>

Commands:
  create-tables    Create all database tables
  drop-tables      Drop all database tables  
  reset-db         Reset database (drop and recreate tables)
  create-admin     Create an admin user
  migrate          Run database migrations
  help             Show this help message

Examples:
  python manage.py create-tables
  python manage.py create-admin
  python manage.py reset-db
    """)


async def main():
    """Main function"""
    if len(sys.argv) < 2:
        print_help()
        sys.exit(1)
    
    command = sys.argv[1]
    
    print(f"ELAMS Management - Environment: {settings.environment}")
    print(f"Database URL: {settings.database_url}")
    print()
    
    try:
        if command == "create-tables":
            await create_tables()
        elif command == "drop-tables":
            await drop_tables()
        elif command == "reset-db":
            await reset_database()
        elif command == "create-admin":
            await create_admin()
        elif command == "migrate":
            await run_migrations()
        elif command == "help":
            print_help()
        else:
            print(f"❌ Unknown command: {command}")
            print_help()
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)
    finally:
        await close_database()


if __name__ == "__main__":
    asyncio.run(main())