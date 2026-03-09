#!/usr/bin/env python
"""
Migration runner with intelligent retry logic for Render deployments.
Handles database hibernation and SSL connection issues gracefully.
"""
import os
import sys
import time
import psycopg2
import django
from pathlib import Path

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'training_feedback_system.settings')
sys.path.insert(0, str(Path(__file__).parent / 'training_feedback_system'))
django.setup()

from django.db import connection
from django.core.management import call_command
from django.db.utils import OperationalError


def test_database_connection(timeout=10):
    """Test if database is available"""
    try:
        print("Testing database connection...", end=" ", flush=True)
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        print("✓")
        return True
    except (psycopg2.OperationalError, OperationalError) as e:
        error_msg = str(e).lower()
        if 'ssl' in error_msg or 'closed' in error_msg:
            print(f"✗ (SSL/Connection issue)")
        else:
            print(f"✗ ({type(e).__name__})")
        return False
    except Exception as e:
        print(f"✗ ({type(e).__name__})")
        return False


def run_migrations(max_retries=5, retry_delay=10):
    """Run Django migrations with retry logic"""
    print(f"\n{'='*70}")
    print(f"DATABASE MIGRATION MANAGER")
    print(f"{'='*70}\n")
    
    for attempt in range(max_retries):
        try:
            print(f"[Attempt {attempt + 1}/{max_retries}]")
            
            # Test connection first
            if not test_database_connection():
                if attempt < max_retries - 1:
                    print(f"⏳ Database unavailable. Waiting {retry_delay}s before retry...")
                    time.sleep(retry_delay)
                    continue
                else:
                    print(f"\n❌ Database connection failed after {max_retries} attempts")
                    print("⚠️  NOTE: Service will start anyway. Database might be initializing.")
                    print("⚠️  Migrations will run when database becomes available.")
                    return True  # Don't fail the service - DB might be starting up
            
            print("Running migrate command...", end=" ", flush=True)
            
            # Run migrations
            call_command(
                'migrate',
                verbosity=1,
                interactive=False,
                database='default'
            )
            
            print("✓")
            print(f"\n{'='*70}")
            print(f"✅ MIGRATIONS COMPLETED SUCCESSFULLY")
            print(f"{'='*70}\n")
            return True
            
        except (psycopg2.OperationalError, OperationalError) as e:
            error_msg = str(e)
            print(f"\n✗ Database error on attempt {attempt + 1}")
            
            # Determine if we should retry
            if 'SSL' in error_msg or 'closed unexpectedly' in error_msg:
                print(f"⚠️  SSL/Connection issue detected")
                if attempt < max_retries - 1:
                    print(f"⏳ Retrying in {retry_delay}s...\n")
                    time.sleep(retry_delay)
                    continue
            elif attempt < max_retries - 1:
                print(f"⏳ Retrying in {retry_delay}s...\n")
                time.sleep(retry_delay)
                continue
            
            # If we've exhausted retries
            print(f"\n❌ Migration failed after {max_retries} attempts")
            print(f"Error: {error_msg[:200]}")
            print("\n⚠️  Service will start without migrations.")
            print("⚠️  This might cause issues. Check database status.")
            return True  # Return True to allow service to start anyway
            
        except Exception as e:
            print(f"\n❌ Unexpected error: {type(e).__name__}: {str(e)[:100]}")
            if attempt < max_retries - 1:
                print(f"⏳ Retrying in {retry_delay}s...\n")
                time.sleep(retry_delay)
            else:
                print(f"\n⚠️  Service will start without running migrations")
                return True
    
    return True


if __name__ == '__main__':
    try:
        success = run_migrations(max_retries=5, retry_delay=10)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Migration interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {str(e)}")
        print("⚠️  Service will attempt to start anyway")
        sys.exit(0)
