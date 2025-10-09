"""
User Analytics Module
Provides analytics and insights for tenant users
"""

from modules.database import get_db_connection
from datetime import datetime, timedelta
import json

def get_user_activity_analytics(user_id):
    """
    Get comprehensive activity analytics for a specific user
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get user's viewed properties
        cursor.execute("""
            SELECT DISTINCT pv.property_id, h.title, h.price, h.property_type, 
                   r.name as region_name, pv.viewed_at
            FROM property_views pv
            JOIN houses h ON pv.property_id = h.id
            LEFT JOIN regions r ON h.region_id = r.id
            WHERE pv.user_id = %s
            ORDER BY pv.viewed_at DESC
            LIMIT 20
        """, (user_id,))
        viewed_properties = cursor.fetchall()
        
        # Get user's search history
        cursor.execute("""
            SELECT search_term, filters_applied, searched_at, results_count
            FROM search_analytics
            WHERE user_id = %s
            ORDER BY searched_at DESC
            LIMIT 15
        """, (user_id,))
        search_history = cursor.fetchall()
        
        # Get user's favorites (if favorites table exists)
        favorites = []
        try:
            cursor.execute("""
                SELECT f.property_id, h.title, h.price, h.property_type, 
                       r.name as region_name, f.created_at
                FROM user_favorites f
                JOIN houses h ON f.property_id = h.id
                LEFT JOIN regions r ON h.region_id = r.id
                WHERE f.user_id = %s
                ORDER BY f.created_at DESC
            """, (user_id,))
            favorites = cursor.fetchall()
        except:
            # Favorites table doesn't exist yet
            pass
        
        # Get user's saved searches (if saved_searches table exists)
        saved_searches = []
        try:
            cursor.execute("""
                SELECT id, search_name, search_term, filters_applied, created_at
                FROM user_saved_searches
                WHERE user_id = %s
                ORDER BY created_at DESC
            """, (user_id,))
            saved_searches = cursor.fetchall()
        except:
            # Saved searches table doesn't exist yet
            pass
        
        # Calculate user preferences
        preferences = calculate_user_preferences(user_id, viewed_properties, search_history)
        
        # Get recommended properties
        recommendations = get_property_recommendations(user_id, preferences)
        
        # Get user engagement summary
        engagement_summary = get_user_engagement_summary(user_id)
        
        return {
            'viewed_properties': viewed_properties,
            'search_history': search_history,
            'favorites': favorites,
            'saved_searches': saved_searches,
            'preferences': preferences,
            'recommendations': recommendations,
            'engagement_summary': engagement_summary
        }
        
    except Exception as e:
        print(f"Error getting user analytics: {e}")
        return {}
    finally:
        cursor.close()
        conn.close()

def calculate_user_preferences(user_id, viewed_properties, search_history):
    """Calculate user preferences based on their activity"""
    preferences = {
        'preferred_regions': [],
        'preferred_property_types': [],
        'price_range': {'min': 0, 'max': 0},
        'search_patterns': [],
        'most_searched_terms': []
    }
    
    if not viewed_properties and not search_history:
        return preferences
    
    # Analyze viewed properties
    regions = {}
    property_types = {}
    prices = []
    
    for prop in viewed_properties:
        # Region preferences
        if prop['region_name']:
            regions[prop['region_name']] = regions.get(prop['region_name'], 0) + 1
        
        # Property type preferences
        if prop['property_type']:
            property_types[prop['property_type']] = property_types.get(prop['property_type'], 0) + 1
        
        # Price preferences
        if prop['price']:
            prices.append(float(prop['price']))
    
    # Analyze search history
    search_terms = {}
    for search in search_history:
        if search['search_term']:
            search_terms[search['search_term']] = search_terms.get(search['search_term'], 0) + 1
        
        # Parse filters
        if search['filters_applied']:
            try:
                filters = json.loads(search['filters_applied'].replace("'", '"'))
                if 'min_price' in filters:
                    prices.append(float(filters['min_price']))
                if 'max_price' in filters:
                    prices.append(float(filters['max_price']))
            except:
                pass
    
    # Calculate preferences
    preferences['preferred_regions'] = sorted(regions.items(), key=lambda x: x[1], reverse=True)[:3]
    preferences['preferred_property_types'] = sorted(property_types.items(), key=lambda x: x[1], reverse=True)[:3]
    preferences['most_searched_terms'] = sorted(search_terms.items(), key=lambda x: x[1], reverse=True)[:5]
    
    if prices:
        preferences['price_range'] = {
            'min': min(prices),
            'max': max(prices),
            'average': sum(prices) / len(prices)
        }
    
    return preferences

def get_property_recommendations(user_id, preferences):
    """Get property recommendations based on user preferences"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Build recommendation query based on preferences
        query = """
            SELECT h.*, r.name as region_name, n.name as neighborhood_name
            FROM houses h
            LEFT JOIN regions r ON h.region_id = r.id
            LEFT JOIN neighborhoods n ON h.neighborhood_id = n.id
            WHERE 1=1
        """
        params = []
        
        # Add region filter if user has preferences
        if preferences['preferred_regions']:
            region_names = [region[0] for region in preferences['preferred_regions']]
            placeholders = ','.join(['%s'] * len(region_names))
            query += f" AND r.name IN ({placeholders})"
            params.extend(region_names)
        
        # Add property type filter
        if preferences['preferred_property_types']:
            prop_types = [ptype[0] for ptype in preferences['preferred_property_types']]
            placeholders = ','.join(['%s'] * len(prop_types))
            query += f" AND h.property_type IN ({placeholders})"
            params.extend(prop_types)
        
        # Add price range filter
        if preferences['price_range']['min'] > 0 and preferences['price_range']['max'] > 0:
            query += " AND h.price BETWEEN %s AND %s"
            params.extend([preferences['price_range']['min'], preferences['price_range']['max']])
        
        query += " ORDER BY h.created_at DESC LIMIT 6"
        
        cursor.execute(query, params)
        recommendations = cursor.fetchall()
        
        # Parse image paths
        for rec in recommendations:
            if rec['image_paths']:
                try:
                    if isinstance(rec['image_paths'], str):
                        rec['image_paths'] = json.loads(rec['image_paths'].replace("'", '"'))
                except:
                    rec['image_paths'] = []
            else:
                rec['image_paths'] = []
        
        return recommendations
        
    except Exception as e:
        print(f"Error getting recommendations: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def get_user_engagement_summary(user_id):
    """Get user engagement summary"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Get engagement data
        cursor.execute("""
            SELECT login_count, session_duration, pages_viewed, 
                   properties_viewed, searches_performed, last_updated
            FROM user_engagement
            WHERE user_id = %s
        """, (user_id,))
        
        result = cursor.fetchone()
        if result:
            return {
                'login_count': result[0] or 0,
                'total_session_duration': result[1] or 0,
                'pages_viewed': result[2] or 0,
                'properties_viewed': result[3] or 0,
                'searches_performed': result[4] or 0,
                'last_updated': result[5]
            }
        else:
            return {
                'login_count': 0,
                'total_session_duration': 0,
                'pages_viewed': 0,
                'properties_viewed': 0,
                'searches_performed': 0,
                'last_updated': None
            }
            
    except Exception as e:
        print(f"Error getting engagement summary: {e}")
        return {}
    finally:
        cursor.close()
        conn.close()

def add_to_favorites(user_id, property_id):
    """Add a property to user's favorites"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if favorites table exists, create if not
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_favorites (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                property_id INT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (property_id) REFERENCES houses(id),
                UNIQUE KEY unique_favorite (user_id, property_id)
            )
        """)
        
        # Add to favorites
        cursor.execute("""
            INSERT INTO user_favorites (user_id, property_id)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE created_at = CURRENT_TIMESTAMP
        """, (user_id, property_id))
        
        conn.commit()
        return True
        
    except Exception as e:
        print(f"Error adding to favorites: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def remove_from_favorites(user_id, property_id):
    """Remove a property from user's favorites"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            DELETE FROM user_favorites
            WHERE user_id = %s AND property_id = %s
        """, (user_id, property_id))
        
        conn.commit()
        return True
        
    except Exception as e:
        print(f"Error removing from favorites: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def save_search(user_id, search_name, search_term, filters_applied):
    """Save a user's search"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if saved_searches table exists, create if not
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_saved_searches (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                search_name VARCHAR(255) NOT NULL,
                search_term VARCHAR(255),
                filters_applied TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # Save search
        cursor.execute("""
            INSERT INTO user_saved_searches (user_id, search_name, search_term, filters_applied)
            VALUES (%s, %s, %s, %s)
        """, (user_id, search_name, search_term, filters_applied))
        
        conn.commit()
        return True
        
    except Exception as e:
        print(f"Error saving search: {e}")
        return False
    finally:
        cursor.close()
        conn.close()
