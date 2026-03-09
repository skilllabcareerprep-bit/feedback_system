#!/usr/bin/env python
"""
Migration runner with intelligent retry logic for Render deployments.
Handles database hibernation and SSL connection issues gracefully.
Uses subprocess to avoid early Django initialization.
"""
import os
import sys
import time
import subprocess
import signal


class TimeoutError(Exception):
    pass


def timeout_handler(signum, frame):
    raise TimeoutError("Migration command timed out")


def run_migrate_command(timeout=30):
    """Run a single migrate command with timeout"""
    try:
        # Set up timeout
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout)
        
        result = subprocess.run(
            [
                sys.executable,
                'training_feedback_system/manage.py',
                'migrate',
                '--noinput',
                '--verbosity=1'
            ],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__)) or '.'
        )
        
        signal.alarm(0)  # Cancel alarm
        
        # Check for SSL errors in output
        output = result.stdout + result.stderr
        has_ssl_error = 'SSL' in output or 'closed unexpectedly' in output or 'ssl' in output.lower()
        
        return result.returncode == 0, output, has_ssl_error
        
    except TimeoutError:
        signal.alarm(0)
        return False, "Command timed out", False
    except Exception as e:
        signal.alarm(0)
        return False, str(e), False


def run_migrations_with_retries(max_retries=5, retry_delay=10):
    """Run migrations with retry logic"""
    print(f"\n{'='*70}")
    print(f"DATABASE MIGRATION MANAGER")
    print(f"{'='*70}\n")
    
    last_output = ""
    
    for attempt in range(max_retries):
        print(f"[Attempt {attempt + 1}/{max_retries}]")
        
        success, output, has_ssl_error = run_migrate_command(timeout=30)
        last_output = output
        
        if success:
            print("Running migration command...✓\n")
            print(f"{'='*70}")
            print(f"✅ MIGRATIONS COMPLETED SUCCESSFULLY")
            print(f"{'='*70}\n")
            return 0  # Success
        
        # Check if it's an SSL/connection error
        if has_ssl_error or 'connection' in output.lower():
            print(f"Running migration command...✗ (Connection/SSL issue)")
            if attempt < max_retries - 1:
                print(f"⏳ Database might be hibernating. Waiting {retry_delay}s...\n")
                time.sleep(retry_delay)
            continue
        
        # Other errors
        print(f"Running migration command...✗")
        if attempt < max_retries - 1:
            print(f"⏳ Retrying in {retry_delay}s...\n")
            time.sleep(retry_delay)
        else:
            print(f"\n{'='*70}")
            print(f"⚠️  MIGRATION FAILED AFTER {max_retries} ATTEMPTS")
            print(f"{'='*70}")
            print(f"\nLast error output:")
            print(output[:500] if output else "(No output captured)")
            print(f"\n{'='*70}")
            print(f"⚠️  SERVICE WILL START IN DEGRADED MODE")
            print(f"{'='*70}\n")
            return 0  # Return 0 to allow service to start anyway
    
    print(f"\n{'='*70}")
    print(f"⚠️  MIGRATION FAILED - SERVICE STARTING IN DEGRADED MODE")
    print(f"{'='*70}\n")
    return 0  # Allow service to start anyway


if __name__ == '__main__':
    try:
        exit_code = run_migrations_with_retries(max_retries=5, retry_delay=10)
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️  Migration interrupted by user")
        sys.exit(0)  # Still allow service to start
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        print("⚠️  Service will attempt to start anyway")
        sys.exit(0)  # Still allow service to start
