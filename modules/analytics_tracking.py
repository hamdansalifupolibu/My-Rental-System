from modules.database import get_db_connection
from datetime import datetime, date
import json

def track_property_view(property_id, user_id=None, ip_address=None, user_agent=None, referrer=None, session_id=None):
    """Track when a property is viewed"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO property_views 
            (property_id, user_id, ip_address, user_agent, referrer, session_id)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (property_id, user_id, ip_address, user_agent, referrer, session_id))
        
        # Update property performance
        today = date.today()
        cursor.execute("""
            INSERT INTO property_performance 
            (property_id, date, views_count) 
            VALUES (%s, %s, 1)
            ON DUPLICATE KEY UPDATE 
            views_count = views_count + 1
        """, (property_id, today))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error tracking property view: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def track_search(user_id=None, search_term=None, filters_applied=None, results_count=0, ip_address=None, session_id=None):
    """Track search activities"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Convert filters to JSON if it's a dict
        if isinstance(filters_applied, dict):
            filters_json = json.dumps(filters_applied)
        else:
            filters_json = filters_applied
            
        cursor.execute("""
            INSERT INTO search_analytics 
            (user_id, search_term, filters_applied, results_count, ip_address, session_id)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (user_id, search_term, filters_json, results_count, ip_address, session_id))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error tracking search: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def track_user_session(user_id, session_id, ip_address=None, user_agent=None):
    """Track user session start"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO user_sessions 
            (user_id, session_id, ip_address, user_agent)
            VALUES (%s, %s, %s, %s)
        """, (user_id, session_id, ip_address, user_agent))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error tracking user session: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def update_user_engagement(user_id, activity_type, value=1):
    """Update user engagement metrics"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        today = date.today()
        
        # Get current engagement data
        cursor.execute("""
            SELECT * FROM user_engagement 
            WHERE user_id = %s AND date = %s
        """, (user_id, today))
        
        existing = cursor.fetchone()
        
        if existing:
            # Update existing record
            if activity_type == 'login':
                cursor.execute("""
                    UPDATE user_engagement 
                    SET login_count = login_count + %s,
                        engagement_score = engagement_score + 0.1
                    WHERE user_id = %s AND date = %s
                """, (value, user_id, today))
            elif activity_type == 'page_view':
                cursor.execute("""
                    UPDATE user_engagement 
                    SET pages_viewed = pages_viewed + %s,
                        engagement_score = engagement_score + 0.05
                    WHERE user_id = %s AND date = %s
                """, (value, user_id, today))
            elif activity_type == 'property_view':
                cursor.execute("""
                    UPDATE user_engagement 
                    SET properties_viewed = properties_viewed + %s,
                        engagement_score = engagement_score + 0.2
                    WHERE user_id = %s AND date = %s
                """, (value, user_id, today))
            elif activity_type == 'search':
                cursor.execute("""
                    UPDATE user_engagement 
                    SET searches_performed = searches_performed + %s,
                        engagement_score = engagement_score + 0.15
                    WHERE user_id = %s AND date = %s
                """, (value, user_id, today))
        else:
            # Create new record
            engagement_score = 0.1 if activity_type == 'login' else 0.05
            cursor.execute("""
                INSERT INTO user_engagement 
                (user_id, date, login_count, pages_viewed, properties_viewed, searches_performed, engagement_score)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (user_id, today, 
                  1 if activity_type == 'login' else 0,
                  1 if activity_type == 'page_view' else 0,
                  1 if activity_type == 'property_view' else 0,
                  1 if activity_type == 'search' else 0,
                  engagement_score))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error updating user engagement: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def update_revenue_analytics(property_id, daily_rent=None, monthly_rent=None, is_occupied=False):
    """Update revenue analytics for a property"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        today = date.today()
        
        # Get property price if not provided
        if not daily_rent and not monthly_rent:
            cursor.execute("SELECT price FROM houses WHERE id = %s", (property_id,))
            house = cursor.fetchone()
            if house:
                monthly_rent = house[0]
                daily_rent = monthly_rent / 30  # Approximate daily rent
        
        cursor.execute("""
            INSERT INTO revenue_analytics 
            (property_id, date, daily_rent, monthly_rent, is_occupied)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
            daily_rent = VALUES(daily_rent),
            monthly_rent = VALUES(monthly_rent),
            is_occupied = VALUES(is_occupied)
        """, (property_id, today, daily_rent, monthly_rent, is_occupied))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error updating revenue analytics: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def update_geographic_analytics(region_id, property_views=0, property_searches=0, new_listings=0):
    """Update geographic analytics for a region"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        today = date.today()
        
        # Calculate average price for the region
        cursor.execute("""
            SELECT AVG(price) FROM houses 
            WHERE region_id = %s
        """, (region_id,))
        avg_price_result = cursor.fetchone()
        avg_price = avg_price_result[0] if avg_price_result[0] else 0
        
        # Calculate demand score (views + searches)
        demand_score = (property_views * 0.7) + (property_searches * 0.3)
        
        cursor.execute("""
            INSERT INTO geographic_analytics 
            (region_id, date, property_views, property_searches, new_listings, average_price, demand_score)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
            property_views = property_views + VALUES(property_views),
            property_searches = property_searches + VALUES(property_searches),
            new_listings = new_listings + VALUES(new_listings),
            average_price = VALUES(average_price),
            demand_score = (demand_score + VALUES(demand_score)) / 2
        """, (region_id, today, property_views, property_searches, new_listings, avg_price, demand_score))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Error updating geographic analytics: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()

def initialize_analytics_data():
    """Initialize analytics data for existing properties and users"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Initialize revenue analytics for all properties
        cursor.execute("""
            INSERT INTO revenue_analytics (property_id, date, daily_rent, monthly_rent, is_occupied)
            SELECT 
                id, 
                CURRENT_DATE, 
                price / 30, 
                price, 
                CASE WHEN is_occupied = 1 THEN 1 ELSE 0 END
            FROM houses
            WHERE id NOT IN (SELECT DISTINCT property_id FROM revenue_analytics WHERE date = CURRENT_DATE)
        """)
        
        # Initialize user engagement for active users
        cursor.execute("""
            INSERT INTO user_engagement (user_id, date, login_count, engagement_score)
            SELECT 
                id, 
                CURRENT_DATE, 
                login_count, 
                CASE 
                    WHEN last_login >= DATE_SUB(NOW(), INTERVAL 7 DAY) THEN 0.8
                    WHEN last_login >= DATE_SUB(NOW(), INTERVAL 30 DAY) THEN 0.5
                    ELSE 0.1
                END
            FROM users
            WHERE id NOT IN (SELECT DISTINCT user_id FROM user_engagement WHERE date = CURRENT_DATE)
        """)
        
        # Initialize geographic analytics for all regions
        cursor.execute("""
            INSERT INTO geographic_analytics (region_id, date, property_views, property_searches, average_price, demand_score)
            SELECT 
                r.id, 
                CURRENT_DATE, 
                0, 
                0, 
                COALESCE(AVG(h.price), 0),
                0
            FROM regions r
            LEFT JOIN houses h ON r.id = h.region_id
            WHERE r.id NOT IN (SELECT DISTINCT region_id FROM geographic_analytics WHERE date = CURRENT_DATE)
            GROUP BY r.id
        """)
        
        conn.commit()
        print("Analytics data initialized successfully!")
        return True
    except Exception as e:
        print(f"Error initializing analytics data: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()
