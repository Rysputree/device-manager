#!/usr/bin/env python3
"""
Test script to verify the bcrypt password length fix works correctly.
Run this on the other server to test the auth.py changes.
"""

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src.auth.auth import hash_password, verify_password
    print("✅ Successfully imported auth functions")
except ImportError as e:
    print(f"❌ Failed to import auth functions: {e}")
    sys.exit(1)

def test_password_hashing():
    """Test password hashing with various password lengths"""
    
    test_cases = [
        ("Normal password", "TestPassword123!"),
        ("Short password", "Test123"),
        ("Long password (100 chars)", "A" * 100),
        ("Very long password (200 chars)", "B" * 200),
        ("Unicode password", "Test密码123!@#"),
        ("Mixed case long", "Aa" * 50),
    ]
    
    print("\n🧪 Testing password hashing...")
    
    for test_name, password in test_cases:
        try:
            # Test hashing
            hashed = hash_password(password)
            print(f"✅ {test_name}: Hash successful (length: {len(hashed)})")
            
            # Test verification
            verified = verify_password(password, hashed)
            if verified:
                print(f"✅ {test_name}: Verification successful")
            else:
                print(f"❌ {test_name}: Verification failed")
                
        except Exception as e:
            print(f"❌ {test_name}: Error - {e}")
    
    print("\n🎉 Password hashing test completed!")

def test_bcrypt_backend():
    """Test bcrypt backend configuration"""
    try:
        from passlib.context import CryptContext
        from passlib.hash import bcrypt, pbkdf2_sha256
        
        print("\n🔧 Testing bcrypt backend...")
        
        # Test bcrypt directly
        try:
            test_hash = bcrypt.hash("test")
            print("✅ bcrypt direct hashing works")
        except Exception as e:
            print(f"⚠️  bcrypt direct hashing failed: {e}")
        
        # Test pbkdf2_sha256 as fallback
        try:
            test_hash = pbkdf2_sha256.hash("test")
            print("✅ pbkdf2_sha256 fallback works")
        except Exception as e:
            print(f"❌ pbkdf2_sha256 fallback failed: {e}")
            
    except ImportError as e:
        print(f"❌ Failed to import passlib modules: {e}")

if __name__ == "__main__":
    print("🚀 Testing bcrypt password length fix...")
    test_bcrypt_backend()
    test_password_hashing()
    print("\n✨ All tests completed!")
