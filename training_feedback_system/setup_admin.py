#!/usr/bin/env python
import sqlite3
import hashlib
import os
from pathlib import Path

# Path to database
db_path = Path(__file__).parent / 'db.sqlite3'

if not db_path.exists():
    print("❌ Error: db.sqlite3 not found. Run migrations first!")
    print("Run: python manage.py migrate")
    exit(1)

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# Delete old admin if exists
cursor.execute("DELETE FROM auth_user WHERE username='admin'")
print("✓ Deleted old admin user if it existed")

# Create new superuser
# Password needs to be hashed using Django's make_password
# For simplicity, we'll use a pbkdf2 algorithm
import hashlib
import base64

password = 'Feedback@2026'
algorithm = 'pbkdf2_sha256'
iterations = 260000
salt = os.urandom(32)
hash_obj = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, iterations)
password_hash = f"{algorithm}${iterations}${base64.b64encode(salt).decode()}${base64.b64encode(hash_obj).decode()}"

# Insert superuser
cursor.execute("""
    INSERT INTO auth_user 
    (username, first_name, last_name, email, password, is_staff, is_active, is_superuser, last_login, date_joined)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
""", ('admin', '', '', 'admin@skilllab.com', password_hash, 1, 1, 1, None))

conn.commit()
conn.close()

print("✓ Superuser 'admin' created successfully!")
print("✓ Username: admin")
print("✓ Password: Feedback@2026")
