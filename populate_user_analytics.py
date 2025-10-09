#!/usr/bin/env python3
"""
Script to populate user analytics with test data
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.database import get_db_connection
from datetime import datetime, timedelta
import random
import json

def populate_user_analytics():
    """Populate user analytics with test data"""
    print("🔄 Populating User Analytics with Test Data...")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get all users and properties
        cursor.execute("SELECT id FROM users WHERE role = 'tenant'")
        tenant_users = cursor.fetchall()
        
        cursor.execute("SELECT id, title, price, property_type, region_id FROM houses")
        properties = cursor.fetchall()
        
        print(f"👥 Found {len(tenant_users)} tenant users")
        print(f"🏠 Found {len(properties)} properties")
        
        if not tenant_users or not properties:
            print("❌ No tenant users or properties found. Please add some first.")
            return
        
        # Generate test data for each user
        for user_id, in tenant_users:
            print(f"👤 Generating data for user {user_id}")
            
            # Generate property views (random properties)
            viewed_properties = random.sample(properties, random.randint(5, 15))
            for prop_id, title, price, prop_type, region_id in viewed_properties:
                for _ in range(random.randint(1, 3)):  # Multiple views per property
                    view_date = datetime.now() - timedelta(days=random.randint(0, 30))
                    cursor.execute("""
                        INSERT INTO property_views (property_id, user_id, ip_address, user_agent, viewed_at)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (
                        prop_id,
                        user_id,
                        f"192.168.1.{random.randint(1, 255)}",
                        "Mozilla/5.0 (Test Browser)",
                        view_date
                    ))
            
            # Generate search analytics
            search_terms = ["apartment", "house", "2 bedroom", "3 bedroom", "furnished", "unfurnished", "rent", "cheap"]
            for i in range(random.randint(10, 25)):
                search_date = datetime.now() - timedelta(days=random.randint(0, 30))
                search_term = random.choice(search_terms)
                filters = {
                    "min_price": random.randint(500, 1000),
                    "max_price": random.randint(1500, 3000),
                    "property_type": random.choice(["apartment", "house", "studio"]),
                    "region": random.randint(1, 5) if random.choice([True, False]) else None
                }
                
                cursor.execute("""
                    INSERT INTO search_analytics (user_id, search_term, filters_applied, results_count, ip_address, searched_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    user_id,
                    search_term,
                    str(filters),
                    random.randint(1, 10),
                    f"192.168.1.{random.randint(1, 255)}",
                    search_date
                ))
            
            # Generate user engagement data
            cursor.execute("""
                INSERT INTO user_engagement (user_id, login_count, session_duration, pages_viewed, properties_viewed, searches_performed, last_updated)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                login_count = login_count + %s,
                session_duration = session_duration + %s,
                pages_viewed = pages_viewed + %s,
                properties_viewed = properties_viewed + %s,
                searches_performed = searches_performed + %s,
                last_updated = %s
            """, (
                user_id,
                random.randint(5, 20),
                random.randint(300, 1800),  # 5-30 minutes
                random.randint(20, 100),
                random.randint(10, 30),
                random.randint(5, 20),
                datetime.now(),
                random.randint(1, 5),
                random.randint(60, 300),
                random.randint(5, 20),
                random.randint(2, 8),
                random.randint(1, 5),
                datetime.now()
            ))
            
            # Generate some favorites (random properties)
            favorite_properties = random.sample(properties, random.randint(2, 8))
            for prop_id, title, price, prop_type, region_id in favorite_properties:
                try:
                    cursor.execute("""
                        INSERT INTO user_favorites (user_id, property_id, created_at)
                        VALUES (%s, %s, %s)
                        ON DUPLICATE KEY UPDATE created_at = %s
                    """, (
                        user_id,
                        prop_id,
                        datetime.now() - timedelta(days=random.randint(0, 15)),
                        datetime.now() - timedelta(days=random.randint(0, 15))
                    ))
                except:
                    # Table might not exist yet
                    pass
            
            # Generate some saved searches
            search_names = ["My Apartment Search", "Budget Houses", "Furnished Properties", "2 Bedroom Search", "Downtown Properties"]
            for i in range(random.randint(1, 3)):
                search_name = random.choice(search_names)
                search_term = random.choice(search_terms)
                filters = {
                    "min_price": random.randint(500, 1000),
                    "max_price": random.randint(1500, 3000),
                    "property_type": random.choice(["apartment", "house"])
                }
                
                try:
                    cursor.execute("""
                        INSERT INTO user_saved_searches (user_id, search_name, search_term, filters_applied, created_at)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (
                        user_id,
                        search_name,
                        search_term,
                        str(filters),
                        datetime.now() - timedelta(days=random.randint(0, 10))
                    ))
                except:
                    # Table might not exist yet
                    pass
        
        # Commit all changes
        conn.commit()
        print("✅ User analytics data populated successfully!")
        
        # Show summary
        cursor.execute("SELECT COUNT(*) FROM property_views")
        views_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM search_analytics")
        searches_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM user_engagement")
        engagement_count = cursor.fetchone()[0]
        
        try:
            cursor.execute("SELECT COUNT(*) FROM user_favorites")
            favorites_count = cursor.fetchone()[0]
        except:
            favorites_count = 0
        
        try:
            cursor.execute("SELECT COUNT(*) FROM user_saved_searches")
            saved_searches_count = cursor.fetchone()[0]
        except:
            saved_searches_count = 0
        
        print(f"\n📈 Data Summary:")
        print(f"   Property Views: {views_count}")
        print(f"   Search Analytics: {searches_count}")
        print(f"   User Engagement: {engagement_count}")
        print(f"   User Favorites: {favorites_count}")
        print(f"   Saved Searches: {saved_searches_count}")
        print(f"\n🎯 Now visit /user-analytics to see your personal analytics!")
        
    except Exception as e:
        print(f"❌ Error populating data: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    populate_user_analytics()
