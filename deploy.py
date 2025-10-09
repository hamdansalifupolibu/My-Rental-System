#!/usr/bin/env python3
"""
GhanaRentals Deployment Script
This script helps prepare your application for production deployment
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_requirements():
    """Check if all required files exist"""
    required_files = [
        'requirements.txt',
        'wsgi.py',
        'app.py',
        'config_production.py',
        'render.yaml'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing required files: {', '.join(missing_files)}")
        return False
    
    print("✅ All required files present")
    return True

def check_environment_variables():
    """Check if environment variables are properly configured"""
    env_file = Path('.env')
    if env_file.exists():
        print("✅ .env file found")
        return True
    else:
        print("⚠️  .env file not found. Make sure to set environment variables in Render dashboard")
        return True

def check_database_config():
    """Check database configuration"""
    try:
        with open('modules/database.py', 'r') as f:
            content = f.read()
            if 'os.environ.get' in content:
                print("✅ Database configuration uses environment variables")
                return True
            else:
                print("❌ Database configuration needs to use environment variables")
                return False
    except FileNotFoundError:
        print("❌ modules/database.py not found")
        return False

def check_templates():
    """Check if templates use url_for instead of hardcoded links"""
    template_dir = Path('templates')
    if not template_dir.exists():
        print("❌ templates directory not found")
        return False
    
    issues = []
    for template_file in template_dir.rglob('*.html'):
        try:
            with open(template_file, 'r') as f:
                content = f.read()
                # Check for common hardcoded patterns
                if 'href="/' in content and 'url_for' not in content:
                    issues.append(f"{template_file}: Contains hardcoded links")
        except Exception as e:
            issues.append(f"{template_file}: Error reading file - {e}")
    
    if issues:
        print("⚠️  Template issues found:")
        for issue in issues:
            print(f"   - {issue}")
        return False
    else:
        print("✅ Templates appear to use proper URL routing")
        return True

def create_logs_directory():
    """Create logs directory for production"""
    logs_dir = Path('logs')
    if not logs_dir.exists():
        logs_dir.mkdir()
        print("✅ Created logs directory")
    else:
        print("✅ Logs directory already exists")

def check_static_files():
    """Check if static files exist"""
    static_dir = Path('static')
    if static_dir.exists():
        print("✅ Static files directory exists")
        return True
    else:
        print("❌ Static files directory not found")
        return False

def generate_secret_key():
    """Generate a secure secret key"""
    import secrets
    secret_key = secrets.token_hex(32)
    print(f"🔑 Generated secret key: {secret_key}")
    print("   Add this to your environment variables as SECRET_KEY")
    return secret_key

def main():
    """Main deployment check function"""
    print("🚀 GhanaRentals Deployment Check")
    print("=" * 40)
    
    checks = [
        ("Required Files", check_requirements),
        ("Environment Variables", check_environment_variables),
        ("Database Configuration", check_database_config),
        ("Template URLs", check_templates),
        ("Static Files", check_static_files),
    ]
    
    all_passed = True
    
    for check_name, check_func in checks:
        print(f"\n📋 Checking {check_name}...")
        if not check_func():
            all_passed = False
    
    print(f"\n📁 Creating necessary directories...")
    create_logs_directory()
    
    print(f"\n🔑 Security...")
    generate_secret_key()
    
    print("\n" + "=" * 40)
    if all_passed:
        print("✅ All checks passed! Your application is ready for deployment.")
        print("\n📝 Next steps:")
        print("1. Push your code to GitHub")
        print("2. Create a new Web Service on Render")
        print("3. Set environment variables in Render dashboard")
        print("4. Deploy and test your application")
    else:
        print("❌ Some checks failed. Please fix the issues above before deploying.")
        sys.exit(1)

if __name__ == "__main__":
    main()
