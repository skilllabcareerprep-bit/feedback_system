#!/usr/bin/env python
"""
Migration runner with retry logic for Render deployments.
Handles database hibernation gracefully.
"""
import os
import sys
import time
import subprocess

def run_migrations(max_retries=5, retry_delay=5):
    """Run Django migrations with retry logic"""
    for attempt in range(max_retries):
        try:
            print(f"\n{'='*60}")
            print(f"Migration Attempt {attempt + 1} of {max_retries}")
            print(f"{'='*60}\n")
            
            # Run migrations
            result = subprocess.run(
                [
                    sys.executable,
                    'training_feedback_system/manage.py',
                    'migrate',
                    '--noinput',
                    '--verbosity=2'
                ],
                cwd=os.path.dirname(os.path.abspath(__file__)) or '.',
                capture_output=False
            )
            
            if result.returncode == 0:
                print("\n✓ Migrations completed successfully!")
                return True
            else:
                print(f"\n✗ Migration failed with exit code {result.returncode}")
                if attempt < max_retries - 1:
                    print(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    
        except Exception as e:
            print(f"\n✗ Error: {str(e)}")
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
    
    print("\n✗ All migration attempts failed")
    return False

if __name__ == '__main__':
    success = run_migrations(max_retries=5, retry_delay=10)
    sys.exit(0 if success else 1)
