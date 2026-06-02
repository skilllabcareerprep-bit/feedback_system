#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from pathlib import Path


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'training_feedback_system.settings')

    # Allow importing root-level helper modules like migrate_with_retry.py
    project_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(project_root))

    if len(sys.argv) > 1 and sys.argv[1] == 'migrate':
        try:
            import migrate_with_retry
        except ImportError:
            pass
        else:
            exit_code = migrate_with_retry.run_migrations_with_retries(max_retries=5, retry_delay=10)
            if exit_code == 0:
                return
            sys.exit(exit_code)

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
