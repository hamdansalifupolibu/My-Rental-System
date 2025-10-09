"""
Landlord Revenue Analytics Module
Provides revenue tracking and analytics for individual landlords
"""

from modules.database import get_db_connection
from datetime import datetime, timedelta
import json

def get_landlord_revenue_metrics(landlord_id):
    """
    Get comprehensive revenue analytics for a specific landlord
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get landlord's properties
        cursor.execute("""
            SELECT id, title, price, property_type, region_id, created_at
            FROM houses 
            WHERE landlord_id = %s
        """, (landlord_id,))
        properties = cursor.fetchall()
        
        if not properties:
            return {
                'total_properties': 0,
                'monthly_revenue': 0,
                'annual_revenue': 0,
                'occupancy_rate': 0,
                'portfolio_performance': [],
                'best_performing_property': None,
                'revenue_trends': [],
                'property_breakdown': []
            }
        
        # Calculate basic metrics
        total_properties = len(properties)
        total_monthly_revenue = sum(float(prop['price']) for prop in properties)
        total_annual_revenue = total_monthly_revenue * 12
        
        # Get occupancy data (simplified - assuming all properties are occupied if they exist)
        # In a real system, you'd track actual occupancy vs availability
        occupancy_rate = 85.0  # Placeholder - would be calculated from actual occupancy data
        
        # Get property performance data
        property_performance = []
        for prop in properties:
            # Simulate some performance metrics
            views = get_property_views(prop['id'])
            searches = get_property_searches(prop['id'])
            
            performance_score = calculate_performance_score(views, searches, prop['price'])
            
            property_performance.append({
                'property_id': prop['id'],
                'title': prop['title'],
                'monthly_rent': float(prop['price']),
                'annual_revenue': float(prop['price']) * 12,
                'views': views,
                'searches': searches,
                'performance_score': performance_score,
                'property_type': prop['property_type'],
                'region_id': prop['region_id']
            })
        
        # Sort by performance score
        property_performance.sort(key=lambda x: x['performance_score'], reverse=True)
        
        # Get best performing property
        best_performing = property_performance[0] if property_performance else None
        
        # Calculate revenue trends (last 6 months)
        revenue_trends = calculate_revenue_trends(landlord_id, properties)
        
        # Property breakdown by type
        property_breakdown = get_property_type_breakdown(properties)
        
        return {
            'total_properties': total_properties,
            'monthly_revenue': total_monthly_revenue,
            'annual_revenue': total_annual_revenue,
            'occupancy_rate': occupancy_rate,
            'portfolio_performance': property_performance,
            'best_performing_property': best_performing,
            'revenue_trends': revenue_trends,
            'property_breakdown': property_breakdown,
            'average_monthly_rent': total_monthly_revenue / total_properties if total_properties > 0 else 0,
            'revenue_growth': calculate_revenue_growth(revenue_trends)
        }
        
    except Exception as e:
        print(f"Error getting landlord revenue metrics: {e}")
        return {}
    finally:
        cursor.close()
        conn.close()

def get_property_views(property_id):
    """Get total views for a property"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT COUNT(*) FROM property_views 
            WHERE property_id = %s
        """, (property_id,))
        result = cursor.fetchone()
        return result[0] if result else 0
    except:
        return 0
    finally:
        cursor.close()
        conn.close()

def get_property_searches(property_id):
    """Get total searches for a property"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT COUNT(*) FROM search_analytics 
            WHERE JSON_EXTRACT(filters_applied, '$.property_id') = %s
        """, (property_id,))
        result = cursor.fetchone()
        return result[0] if result else 0
    except:
        return 0
    finally:
        cursor.close()
        conn.close()

def calculate_performance_score(views, searches, price):
    """Calculate a performance score for a property"""
    # Simple scoring algorithm
    view_score = min(views * 0.1, 50)  # Max 50 points for views
    search_score = min(searches * 0.2, 30)  # Max 30 points for searches
    price_score = min(float(price) / 100, 20)  # Max 20 points for price
    
    return view_score + search_score + price_score

def calculate_revenue_trends(landlord_id, properties):
    """Calculate revenue trends over the last 6 months"""
    trends = []
    
    for i in range(6):
        month_date = datetime.now() - timedelta(days=30*i)
        month_name = month_date.strftime('%B %Y')
        
        # For now, use current prices as historical data
        # In a real system, you'd track actual historical revenue
        monthly_revenue = sum(float(prop['price']) for prop in properties)
        
        trends.append({
            'month': month_name,
            'revenue': monthly_revenue,
            'properties_count': len(properties)
        })
    
    return list(reversed(trends))  # Oldest to newest

def get_property_type_breakdown(properties):
    """Get breakdown of properties by type"""
    type_counts = {}
    type_revenue = {}
    
    for prop in properties:
        prop_type = prop['property_type'] or 'Unknown'
        price = float(prop['price'])
        
        if prop_type in type_counts:
            type_counts[prop_type] += 1
            type_revenue[prop_type] += price
        else:
            type_counts[prop_type] = 1
            type_revenue[prop_type] = price
    
    breakdown = []
    for prop_type, count in type_counts.items():
        breakdown.append({
            'type': prop_type,
            'count': count,
            'monthly_revenue': type_revenue[prop_type],
            'average_rent': type_revenue[prop_type] / count
        })
    
    return breakdown

def calculate_revenue_growth(revenue_trends):
    """Calculate revenue growth percentage"""
    if len(revenue_trends) < 2:
        return 0
    
    current_revenue = revenue_trends[-1]['revenue']
    previous_revenue = revenue_trends[-2]['revenue']
    
    if previous_revenue == 0:
        return 0
    
    growth = ((current_revenue - previous_revenue) / previous_revenue) * 100
    return round(growth, 1)

def get_landlord_property_analytics(landlord_id, property_id):
    """Get detailed analytics for a specific property"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get property details
        cursor.execute("""
            SELECT h.*, r.name as region_name, n.name as neighborhood_name
            FROM houses h
            LEFT JOIN regions r ON h.region_id = r.id
            LEFT JOIN neighborhoods n ON h.neighborhood_id = n.id
            WHERE h.id = %s AND h.landlord_id = %s
        """, (property_id, landlord_id))
        
        property_data = cursor.fetchone()
        if not property_data:
            return None
        
        # Get analytics data
        views = get_property_views(property_id)
        searches = get_property_searches(property_id)
        
        # Calculate performance metrics
        monthly_rent = float(property_data['price'])
        annual_revenue = monthly_rent * 12
        
        return {
            'property': property_data,
            'monthly_rent': monthly_rent,
            'annual_revenue': annual_revenue,
            'total_views': views,
            'total_searches': searches,
            'performance_score': calculate_performance_score(views, searches, monthly_rent),
            'occupancy_rate': 85.0,  # Placeholder
            'last_updated': datetime.now().strftime('%Y-%m-%d')
        }
        
    except Exception as e:
        print(f"Error getting property analytics: {e}")
        return None
    finally:
        cursor.close()
        conn.close()
