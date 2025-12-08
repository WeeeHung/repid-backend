#!/usr/bin/env python3
"""
Diagnostic script to test Supabase database connection.
This helps verify your connection string and diagnose connection issues.
"""

import os
import sys
import re
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent))

try:
    from app.database import DatabaseSettings, DATABASE_URL
    from sqlalchemy import create_engine, text
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you're in the repid-backend directory and have activated your virtual environment")
    sys.exit(1)


def test_dns_resolution(hostname: str) -> bool:
    """Test if hostname can be resolved"""
    import socket
    try:
        socket.gethostbyname(hostname)
        return True
    except socket.gaierror:
        return False


def extract_project_ref(hostname: str) -> str:
    """Extract project reference from hostname"""
    match = re.match(r'db\.(.+)\.supabase\.co', hostname)
    return match.group(1) if match else "unknown"


def main():
    print("=" * 60)
    print("Supabase Database Connection Diagnostic")
    print("=" * 60)
    print()
    
    # Load settings
    try:
        settings = DatabaseSettings()
        print("✓ Successfully loaded database settings from .env")
    except Exception as e:
        print(f"✗ Error loading settings: {e}")
        return
    
    print()
    print("Connection String Analysis:")
    print("-" * 60)
    
    # Extract information from connection string
    hostname_match = re.search(r'@([^:]+):', DATABASE_URL)
    hostname = hostname_match.group(1) if hostname_match else "unknown"
    project_ref = extract_project_ref(hostname)
    
    print(f"Hostname: {hostname}")
    print(f"Project Reference ID: {project_ref}")
    
    # Check SUPABASE_URL for comparison
    try:
        from app.services.storage import StorageSettings
        storage_settings = StorageSettings()
        supabase_url = storage_settings.supabase_url
        print(f"SUPABASE_URL: {supabase_url}")
        
        # Extract project ref from SUPABASE_URL
        url_match = re.search(r'https://([^.]+)\.supabase\.co', supabase_url)
        if url_match:
            url_project_ref = url_match.group(1)
            print(f"Project Reference from SUPABASE_URL: {url_project_ref}")
            
            if project_ref != url_project_ref:
                print()
                print("⚠️  WARNING: Project reference IDs don't match!")
                print(f"   Database URL uses: {project_ref}")
                print(f"   SUPABASE_URL uses: {url_project_ref}")
                print("   These should match. Check your SUPABASE_DB_URL.")
    except Exception as e:
        print(f"Could not load SUPABASE_URL: {e}")
    
    print()
    print("DNS Resolution Test:")
    print("-" * 60)
    
    if test_dns_resolution(hostname):
        print(f"✓ Hostname {hostname} resolves successfully")
    else:
        print(f"✗ Hostname {hostname} cannot be resolved")
        print()
        print("Possible causes:")
        print("  1. Project reference ID is incorrect")
        print("  2. Supabase project has been deleted or paused")
        print("  3. Network/DNS issues")
        print()
        print("To fix:")
        print("  1. Go to Supabase Dashboard > Your Project")
        print("  2. Check your project URL (should be: https://[PROJECT-REF].supabase.co)")
        print("  3. Go to Settings > Database")
        print("  4. Copy the connection string under 'Connection string' > 'URI'")
        print("  5. Replace [YOUR-PASSWORD] with your actual database password")
        return
    
    print()
    print("Database Connection Test:")
    print("-" * 60)
    
    try:
        engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,
            connect_args={"connect_timeout": 10}
        )
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print("✓ Successfully connected to database!")
            print(f"  PostgreSQL version: {version[:50]}...")
            
            # Test query
            result = conn.execute(text("SELECT current_database();"))
            db_name = result.fetchone()[0]
            print(f"  Current database: {db_name}")
            
    except Exception as e:
        print(f"✗ Failed to connect to database: {e}")
        print()
        if "could not translate host name" in str(e).lower():
            print("This is a DNS resolution error. The hostname cannot be found.")
        elif "password authentication failed" in str(e).lower():
            print("Password authentication failed. Check your database password.")
        elif "timeout" in str(e).lower():
            print("Connection timeout. Check your network connection.")
        else:
            print("Check the error message above for details.")
        return
    
    print()
    print("=" * 60)
    print("✓ All tests passed! Your database connection is working.")
    print("=" * 60)


if __name__ == "__main__":
    main()

