#!/usr/bin/env python3
"""
Simple script to add users to the authentication database.
For admin use only - creates users with hashed passwords.
"""
import sys
import os
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from dotenv import load_dotenv
from api.auth.utils import get_password_hash
from api.database.connection import get_database

# Load environment variables
load_dotenv(project_root / '.env')

def add_user(username: str, password: str, email: str = None):
    """Add a new user to the database"""
    try:
        db = get_database()
        
        # Check if user already exists
        existing_user = db.users.find_one({"username": username})
        if existing_user:
            print(f"❌ User '{username}' already exists!")
            return False
        
        # Hash the password
        hashed_password = get_password_hash(password)
        
        # Create user document
        user_doc = {
            "username": username,
            "email": email,
            "hashed_password": hashed_password,
            "is_active": True,
            "created_at": datetime.utcnow(),
            "last_login": None
        }
        
        # Insert user
        result = db.users.insert_one(user_doc)
        print(f"✅ User '{username}' created successfully! ID: {result.inserted_id}")
        return True
        
    except Exception as e:
        print(f"❌ Error creating user: {e}")
        return False

def main():
    """Main function"""
    if len(sys.argv) < 3:
        print("Usage: python scripts/add_user.py <username> <password> [email]")
        print("Example: python scripts/add_user.py admin mypassword123 admin@example.com")
        sys.exit(1)
    
    username = sys.argv[1]
    password = sys.argv[2]
    email = sys.argv[3] if len(sys.argv) > 3 else None
    
    print(f"Adding user: {username}")
    if email:
        print(f"Email: {email}")
    
    success = add_user(username, password, email)
    if success:
        print("\n🎉 User added successfully!")
        print("You can now use these credentials to login via the /login endpoint.")
    else:
        print("\n💥 Failed to add user!")
        sys.exit(1)

if __name__ == "__main__":
    main()