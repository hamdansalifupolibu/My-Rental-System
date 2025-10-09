#!/usr/bin/env python3
"""
Comprehensive Route Testing Script
Tests all routes in the application to ensure they work correctly
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
from modules.database import get_db_connection
import requests
import json

def test_routes():
    """Test all routes in the application"""
    print("🧪 Testing All Routes in GhanaRentals Application")
    print("=" * 60)
    
    # Test client
    client = app.test_client()
    
    # Routes to test
    routes_to_test = [
        # Public routes
        {'url': '/', 'method': 'GET', 'expected_status': 200, 'description': 'Home page'},
        {'url': '/houses', 'method': 'GET', 'expected_status': 200, 'description': 'Browse houses'},
        {'url': '/login', 'method': 'GET', 'expected_status': 200, 'description': 'Login page'},
        {'url': '/register', 'method': 'GET', 'expected_status': 200, 'description': 'Register page'},
        
        # Auth routes
        {'url': '/profile', 'method': 'GET', 'expected_status': 302, 'description': 'Profile (redirects to login)'},
        {'url': '/logout', 'method': 'GET', 'expected_status': 302, 'description': 'Logout'},
        
        # User routes
        {'url': '/tenant-dashboard', 'method': 'GET', 'expected_status': 302, 'description': 'Tenant dashboard (redirects to login)'},
        {'url': '/user-analytics', 'method': 'GET', 'expected_status': 302, 'description': 'User analytics (redirects to login)'},
        
        # Admin routes
        {'url': '/admin/dashboard', 'method': 'GET', 'expected_status': 302, 'description': 'Admin dashboard (redirects to login)'},
        {'url': '/admin/landlord-dashboard', 'method': 'GET', 'expected_status': 302, 'description': 'Landlord dashboard (redirects to login)'},
        {'url': '/admin/landlord-revenue', 'method': 'GET', 'expected_status': 302, 'description': 'Landlord revenue (redirects to login)'},
        {'url': '/admin/add-house', 'method': 'GET', 'expected_status': 302, 'description': 'Add house (redirects to login)'},
        {'url': '/admin/manage-houses', 'method': 'GET', 'expected_status': 302, 'description': 'Manage houses (redirects to login)'},
        {'url': '/admin/manage-users', 'method': 'GET', 'expected_status': 302, 'description': 'Manage users (redirects to login)'},
        
        # Report routes
        {'url': '/report-issue', 'method': 'GET', 'expected_status': 302, 'description': 'Report issue (redirects to login)'},
        {'url': '/my-reports', 'method': 'GET', 'expected_status': 302, 'description': 'My reports (redirects to login)'},
        {'url': '/admin/reports', 'method': 'GET', 'expected_status': 302, 'description': 'Admin reports (redirects to login)'},
        
        # API routes
        {'url': '/chatbot', 'method': 'POST', 'expected_status': 200, 'description': 'Chatbot API'},
    ]
    
    # Test each route
    passed = 0
    failed = 0
    
    for route in routes_to_test:
        try:
            if route['method'] == 'GET':
                response = client.get(route['url'])
            elif route['method'] == 'POST':
                if route['url'] == '/chatbot':
                    response = client.post(route['url'], 
                                         data=json.dumps({'message': 'hello'}),
                                         content_type='application/json')
                else:
                    response = client.post(route['url'])
            
            status_code = response.status_code
            
            if status_code == route['expected_status']:
                print(f"✅ {route['description']}: {route['url']} - Status: {status_code}")
                passed += 1
            else:
                print(f"❌ {route['description']}: {route['url']} - Expected: {route['expected_status']}, Got: {status_code}")
                failed += 1
                
        except Exception as e:
            print(f"❌ {route['description']}: {route['url']} - Error: {str(e)}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All routes are working correctly!")
    else:
        print("⚠️  Some routes need attention.")
    
    return failed == 0

def test_database_connection():
    """Test database connection"""
    print("\n🔗 Testing Database Connection...")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Test basic queries
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM houses")
        house_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM regions")
        region_count = cursor.fetchone()[0]
        
        print(f"✅ Database connection successful!")
        print(f"   Users: {user_count}")
        print(f"   Houses: {house_count}")
        print(f"   Regions: {region_count}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_templates():
    """Test if all templates exist"""
    print("\n📄 Testing Template Files...")
    
    templates_to_check = [
        'user/index.html',
        'user/houses.html',
        'user/house_detail.html',
        'user/tenant_dashboard.html',
        'user/analytics_dashboard.html',
        'auth/login.html',
        'auth/register.html',
        'admin/dashboard.html',
        'landlord/dashboard.html',
        'landlord/revenue_analytics.html',
        'landlord/property_analytics.html',
    ]
    
    passed = 0
    failed = 0
    
    for template in templates_to_check:
        template_path = f"templates/{template}"
        if os.path.exists(template_path):
            print(f"✅ {template}")
            passed += 1
        else:
            print(f"❌ {template} - Missing")
            failed += 1
    
    print(f"\n📊 Template Results: {passed} found, {failed} missing")
    return failed == 0

def main():
    """Main test function"""
    print("🚀 GhanaRentals Application Test Suite")
    print("=" * 60)
    
    # Test database
    db_ok = test_database_connection()
    
    # Test templates
    templates_ok = test_templates()
    
    # Test routes
    routes_ok = test_routes()
    
    print("\n" + "=" * 60)
    print("📋 Final Results:")
    print(f"   Database: {'✅ OK' if db_ok else '❌ FAILED'}")
    print(f"   Templates: {'✅ OK' if templates_ok else '❌ FAILED'}")
    print(f"   Routes: {'✅ OK' if routes_ok else '❌ FAILED'}")
    
    if db_ok and templates_ok and routes_ok:
        print("\n🎉 All tests passed! Your application is ready to go!")
    else:
        print("\n⚠️  Some tests failed. Please check the issues above.")
    
    return db_ok and templates_ok and routes_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
