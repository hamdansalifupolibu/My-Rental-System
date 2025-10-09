#!/usr/bin/env python3
"""
Quick script to populate landlord analytics with test data
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.database import get_db_connection
from datetime import datetime, timedelta
import random

def populate_landlord_analytics():
    """Populate analytics tables with test data for landlords"""
    print("🔄 Populating Landlord Analytics with Test Data...")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get all landlords and their properties
        cursor.execute("""
            SELECT u.id as landlord_id, u.username, h.id as property_id, h.title, h.price
            FROM users u
            JOIN houses h ON h.created_by = u.id
            WHERE u.role IN ('landlord', 'admin')
        """)
        
        landlord_properties = cursor.fetchall()
        print(f"📊 Found {len(landlord_properties)} landlord properties")
        
        if not landlord_properties:
            print("❌ No landlord properties found. Please add some properties first.")
            return
        
        # Generate test data for each property
        for landlord_id, username, property_id, title, price in landlord_properties:
            print(f"🏠 Generating data for {title} (Landlord: {username})")
            
            # Generate property views (last 30 days)
            for i in range(random.randint(10, 50)):
                view_date = datetime.now() - timedelta(days=random.randint(0, 30))
                cursor.execute("""
                    INSERT INTO property_views (property_id, user_id, ip_address, user_agent, viewed_at)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    property_id,
                    random.randint(1, 10) if random.choice([True, False]) else None,
                    f"192.168.1.{random.randint(1, 255)}",
                    "Mozilla/5.0 (Test Browser)",
                    view_date
                ))
            
            # Generate search analytics
            search_terms = ["apartment", "house", "rent", "2 bedroom", "3 bedroom", "furnished"]
            for i in range(random.randint(5, 20)):
                search_date = datetime.now() - timedelta(days=random.randint(0, 30))
                search_term = random.choice(search_terms)
                filters = {
                    "min_price": random.randint(500, 1000),
                    "max_price": random.randint(1500, 3000),
                    "property_type": random.choice(["apartment", "house", "studio"])
                }
                
                cursor.execute("""
                    INSERT INTO search_analytics (user_id, search_term, filters_applied, results_count, ip_address, searched_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    random.randint(1, 10) if random.choice([True, False]) else None,
                    search_term,
                    str(filters),
                    random.randint(1, 10),
                    f"192.168.1.{random.randint(1, 255)}",
                    search_date
                ))
            
            # Generate user engagement data
            for user_id in range(1, 11):
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
                    random.randint(1, 10),
                    random.randint(30, 180),
                    random.randint(5, 50),
                    random.randint(1, 20),
                    random.randint(1, 15),
                    datetime.now(),
                    random.randint(1, 5),
                    random.randint(10, 60),
                    random.randint(2, 10),
                    random.randint(1, 5),
                    random.randint(1, 3),
                    datetime.now()
                ))
        
        # Commit all changes
        conn.commit()
        print("✅ Landlord analytics data populated successfully!")
        
        # Show summary
        cursor.execute("SELECT COUNT(*) FROM property_views")
        views_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM search_analytics")
        searches_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM user_engagement")
        engagement_count = cursor.fetchone()[0]
        
        print(f"\n📈 Data Summary:")
        print(f"   Property Views: {views_count}")
        print(f"   Search Analytics: {searches_count}")
        print(f"   User Engagement: {engagement_count}")
        print(f"\n🎯 Now visit /admin/landlord-revenue to see your analytics!")
        
    except Exception as e:
        print(f"❌ Error populating data: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    populate_landlord_analytics()
