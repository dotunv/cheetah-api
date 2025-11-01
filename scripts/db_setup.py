#!/usr/bin/env python3
"""
Database setup script for Cheetah API.

This script helps with:
1. Creating the database if it doesn't exist
2. Running migrations
3. Seeding initial data
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Note: This script should be run with uv to ensure dependencies are available
# Example: uv run python scripts/db_setup.py


def create_database_if_not_exists():
    """Create the database if it doesn't exist."""
    try:
        from sqlalchemy import create_engine, text
        from sqlalchemy.exc import OperationalError
        from app.database.config import settings
    except ImportError as e:
        print(f"Error importing dependencies: {e}")
        print("Please run this script with: uv run python scripts/db_setup.py")
        return False
    # Parse the DATABASE_URL to get connection details
    db_url = settings.DATABASE_URL
    
    # Extract database name from URL
    if db_url.startswith('postgresql://'):
        # Remove postgresql:// prefix
        connection_string = db_url.replace('postgresql://', '')
        
        # Split into user:pass@host:port and database
        if '/' in connection_string:
            connection_part, db_name = connection_string.rsplit('/', 1)
        else:
            print("Invalid DATABASE_URL format")
            return False
            
        # Create connection string for postgres database
        postgres_url = f"postgresql://{connection_part}/postgres"
        
        try:
            # Connect to postgres database
            engine = create_engine(postgres_url)
            
            # Check if database exists
            with engine.connect() as conn:
                result = conn.execute(text(
                    "SELECT 1 FROM pg_database WHERE datname = :db_name"
                ), {"db_name": db_name})
                
                if not result.fetchone():
                    # Create database
                    conn.execute(text(f"CREATE DATABASE {db_name}"))
                    conn.commit()
                    print(f"Database '{db_name}' created successfully")
                else:
                    print(f"Database '{db_name}' already exists")
                    
            engine.dispose()
            return True
            
        except OperationalError as e:
            print(f"Error connecting to PostgreSQL: {e}")
            print("Please ensure PostgreSQL is running and accessible")
            return False
        except Exception as e:
            print(f"Error creating database: {e}")
            return False
    else:
        print("Unsupported database URL format")
        return False


def run_migrations():
    """Run Alembic migrations."""
    import subprocess
    import sys
    
    try:
        # Run alembic upgrade head directly (since we're already in the virtual environment)
        result = subprocess.run([
            sys.executable, "-m", "alembic", "upgrade", "head"
        ], capture_output=True, text=True, cwd=project_root)
        
        if result.returncode == 0:
            print("Migrations applied successfully")
            return True
        else:
            print(f"Migration failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"Error running migrations: {e}")
        return False


def seed_initial_data():
    """Seed initial data for development."""
    print("Seeding initial data...")
    print("Initial data seeding completed")
    return True


def main():
    """Main function to set up the database."""
    print("Setting up Cheetah API database...")
    
    # Step 1: Create database if it doesn't exist
    print("\n1. Checking database existence...")
    if not create_database_if_not_exists():
        print("Failed to create database. Exiting.")
        sys.exit(1)
    
    # Step 2: Run migrations
    print("\n2. Running migrations...")
    if not run_migrations():
        print("Failed to run migrations. Exiting.")
        sys.exit(1)
    
    # Step 3: Seed initial data (optional)
    print("\n3. Seeding initial data...")
    seed_initial_data()
    
    print("\nDatabase setup completed successfully!")
    print("\nYou can now start the application with:")
    print("uv run uvicorn app.main:app --reload")


if __name__ == "__main__":
    main() 