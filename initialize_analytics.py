#!/usr/bin/env python3
"""
Initialize Analytics Data
Run this script to set up analytics data for existing properties and users
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.analytics_tracking import initialize_analytics_data

def main():
    print("🚀 Initializing Analytics Data...")
    print("=" * 50)
    
    try:
        success = initialize_analytics_data()
        
        if success:
            print("✅ Analytics data initialized successfully!")
            print("\n📊 What was initialized:")
            print("- Revenue analytics for all properties")
            print("- User engagement data for all users")
            print("- Geographic analytics for all regions")
            print("\n🎯 Next steps:")
            print("1. Update your admin dashboard to use the new metrics")
            print("2. Add tracking calls to your views and routes")
            print("3. Monitor the analytics data as users interact with the system")
        else:
            print("❌ Failed to initialize analytics data")
            print("Check your database connection and table structure")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure all analytics tables are created first")

if __name__ == "__main__":
    main()
