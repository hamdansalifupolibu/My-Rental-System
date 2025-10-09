from modules.database import get_db_connection
from datetime import datetime, timedelta
import json

def get_revenue_analytics():
    """Get comprehensive revenue analytics"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    metrics = {}
    
    try:
        # Total revenue metrics
        cursor.execute("""
            SELECT 
                SUM(daily_rent) as total_daily_rent,
                SUM(monthly_rent) as total_monthly_rent,
                SUM(revenue_generated) as total_revenue,
                AVG(daily_rent) as avg_daily_rent,
                AVG(monthly_rent) as avg_monthly_rent
            FROM revenue_analytics 
            WHERE date >= DATE_SUB(CURRENT_DATE, INTERVAL 30 DAY)
        """)
        revenue_data = cursor.fetchone()
        metrics['revenue_summary'] = revenue_data
        
        # Revenue by property type
        cursor.execute("""
            SELECT 
                h.property_type,
                SUM(ra.revenue_generated) as total_revenue,
                AVG(ra.monthly_rent) as avg_monthly_rent,
                COUNT(DISTINCT h.id) as property_count
            FROM revenue_analytics ra
            JOIN houses h ON ra.property_id = h.id
            WHERE ra.date >= DATE_SUB(CURRENT_DATE, INTERVAL 30 DAY)
            GROUP BY h.property_type
        """)
        metrics['revenue_by_type'] = cursor.fetchall()
        
        # Revenue by region
        cursor.execute("""
            SELECT 
                r.name as region_name,
                SUM(ra.revenue_generated) as total_revenue,
                AVG(ra.monthly_rent) as avg_monthly_rent,
                COUNT(DISTINCT h.id) as property_count
            FROM revenue_analytics ra
            JOIN houses h ON ra.property_id = h.id
            JOIN regions r ON h.region_id = r.id
            WHERE ra.date >= DATE_SUB(CURRENT_DATE, INTERVAL 30 DAY)
            GROUP BY r.id, r.name
        """)
        metrics['revenue_by_region'] = cursor.fetchall()
        
        # Top earning properties
        cursor.execute("""
            SELECT 
                h.title,
                h.property_type,
                SUM(ra.revenue_generated) as total_revenue,
                AVG(ra.monthly_rent) as avg_monthly_rent
            FROM revenue_analytics ra
            JOIN houses h ON ra.property_id = h.id
            WHERE ra.date >= DATE_SUB(CURRENT_DATE, INTERVAL 30 DAY)
            GROUP BY h.id, h.title, h.property_type
            ORDER BY total_revenue DESC
            LIMIT 10
        """)
        metrics['top_earning_properties'] = cursor.fetchall()
        
        # Revenue growth (monthly comparison)
        cursor.execute("""
            SELECT 
                DATE_FORMAT(date, '%Y-%m') as month,
                SUM(revenue_generated) as monthly_revenue
            FROM revenue_analytics 
            WHERE date >= DATE_SUB(CURRENT_DATE, INTERVAL 6 MONTH)
            GROUP BY DATE_FORMAT(date, '%Y-%m')
            ORDER BY month
        """)
        metrics['revenue_growth'] = cursor.fetchall()
        
    except Exception as e:
        print(f"Error getting revenue analytics: {e}")
        metrics = {}
    finally:
        cursor.close()
        conn.close()
    
    return metrics

def get_user_engagement_metrics():
    """Get comprehensive user engagement metrics"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    metrics = {}
    
    try:
        # Overall engagement metrics
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT user_id) as active_users,
                AVG(engagement_score) as avg_engagement,
                SUM(login_count) as total_logins,
                AVG(session_duration) as avg_session_duration,
                AVG(pages_viewed) as avg_pages_per_session
            FROM user_engagement 
            WHERE date >= DATE_SUB(CURRENT_DATE, INTERVAL 30 DAY)
        """)
        metrics['engagement_summary'] = cursor.fetchone()
        
        # User retention metrics
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT user_id) as daily_active_users,
                date
            FROM user_engagement 
            WHERE date >= DATE_SUB(CURRENT_DATE, INTERVAL 30 DAY)
            GROUP BY date
            ORDER BY date
        """)
        metrics['daily_active_users'] = cursor.fetchall()
        
        # Most engaged users
        cursor.execute("""
            SELECT 
                u.username,
                u.full_name,
                u.role,
                AVG(ue.engagement_score) as avg_engagement,
                SUM(ue.login_count) as total_logins,
                SUM(ue.properties_viewed) as total_property_views
            FROM user_engagement ue
            JOIN users u ON ue.user_id = u.id
            WHERE ue.date >= DATE_SUB(CURRENT_DATE, INTERVAL 30 DAY)
            GROUP BY u.id, u.username, u.full_name, u.role
            ORDER BY avg_engagement DESC
            LIMIT 10
        """)
        metrics['most_engaged_users'] = cursor.fetchall()
        
        # User activity by role
        cursor.execute("""
            SELECT 
                u.role,
                COUNT(DISTINCT ue.user_id) as active_users,
                AVG(ue.engagement_score) as avg_engagement,
                AVG(ue.session_duration) as avg_session_duration
            FROM user_engagement ue
            JOIN users u ON ue.user_id = u.id
            WHERE ue.date >= DATE_SUB(CURRENT_DATE, INTERVAL 30 DAY)
            GROUP BY u.role
        """)
        metrics['engagement_by_role'] = cursor.fetchall()
        
        # User journey metrics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_registrations,
                COUNT(CASE WHEN last_login >= DATE_SUB(NOW(), INTERVAL 7 DAY) THEN 1 END) as active_last_week,
                COUNT(CASE WHEN last_login >= DATE_SUB(NOW(), INTERVAL 30 DAY) THEN 1 END) as active_last_month
            FROM users
            WHERE created_at >= DATE_SUB(CURRENT_DATE, INTERVAL 30 DAY)
        """)
        metrics['user_journey'] = cursor.fetchone()
        
    except Exception as e:
        print(f"Error getting user engagement metrics: {e}")
        metrics = {}
    finally:
        cursor.close()
        conn.close()
    
    return metrics

def get_property_performance_metrics():
    """Get comprehensive property performance metrics"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    metrics = {}
    
    try:
        # Overall property performance
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT property_id) as total_properties_tracked,
                SUM(views_count) as total_views,
                SUM(searches_count) as total_searches,
                SUM(contacts_count) as total_contacts,
                AVG(views_count) as avg_views_per_property
            FROM property_performance 
            WHERE date >= DATE_SUB(CURRENT_DATE, INTERVAL 30 DAY)
        """)
        metrics['performance_summary'] = cursor.fetchone()
        
        # Most viewed properties
        cursor.execute("""
            SELECT 
                h.title,
                h.property_type,
                h.price,
                SUM(pp.views_count) as total_views,
                AVG(pp.views_count) as avg_daily_views
            FROM property_performance pp
            JOIN houses h ON pp.property_id = h.id
            WHERE pp.date >= DATE_SUB(CURRENT_DATE, INTERVAL 30 DAY)
            GROUP BY h.id, h.title, h.property_type, h.price
            ORDER BY total_views DESC
            LIMIT 10
        """)
        metrics['most_viewed_properties'] = cursor.fetchall()
        
        # Property performance by type
        cursor.execute("""
            SELECT 
                h.property_type,
                COUNT(DISTINCT pp.property_id) as property_count,
                SUM(pp.views_count) as total_views,
                AVG(pp.views_count) as avg_views_per_property,
                SUM(pp.contacts_count) as total_contacts
            FROM property_performance pp
            JOIN houses h ON pp.property_id = h.id
            WHERE pp.date >= DATE_SUB(CURRENT_DATE, INTERVAL 30 DAY)
            GROUP BY h.property_type
        """)
        metrics['performance_by_type'] = cursor.fetchall()
        
        # Property performance by region
        cursor.execute("""
            SELECT 
                r.name as region_name,
                COUNT(DISTINCT pp.property_id) as property_count,
                SUM(pp.views_count) as total_views,
                AVG(pp.views_count) as avg_views_per_property,
                AVG(h.price) as avg_price
            FROM property_performance pp
            JOIN houses h ON pp.property_id = h.id
            JOIN regions r ON h.region_id = r.id
            WHERE pp.date >= DATE_SUB(CURRENT_DATE, INTERVAL 30 DAY)
            GROUP BY r.id, r.name
        """)
        metrics['performance_by_region'] = cursor.fetchall()
        
        # Conversion rates
        cursor.execute("""
            SELECT 
                h.id,
                h.title,
                SUM(pp.views_count) as total_views,
                SUM(pp.contacts_count) as total_contacts,
                CASE 
                    WHEN SUM(pp.views_count) > 0 
                    THEN ROUND((SUM(pp.contacts_count) / SUM(pp.views_count)) * 100, 2)
                    ELSE 0 
                END as conversion_rate
            FROM property_performance pp
            JOIN houses h ON pp.property_id = h.id
            WHERE pp.date >= DATE_SUB(CURRENT_DATE, INTERVAL 30 DAY)
            GROUP BY h.id, h.title
            HAVING total_views > 0
            ORDER BY conversion_rate DESC
            LIMIT 10
        """)
        metrics['conversion_rates'] = cursor.fetchall()
        
        # Daily performance trends
        cursor.execute("""
            SELECT 
                date,
                SUM(views_count) as daily_views,
                SUM(searches_count) as daily_searches,
                SUM(contacts_count) as daily_contacts
            FROM property_performance 
            WHERE date >= DATE_SUB(CURRENT_DATE, INTERVAL 30 DAY)
            GROUP BY date
            ORDER BY date
        """)
        metrics['daily_trends'] = cursor.fetchall()
        
    except Exception as e:
        print(f"Error getting property performance metrics: {e}")
        metrics = {}
    finally:
        cursor.close()
        conn.close()
    
    return metrics

def get_geographic_analytics():
    """Get comprehensive geographic analytics"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    metrics = {}
    
    try:
        # Regional performance summary
        cursor.execute("""
            SELECT 
                r.name as region_name,
                COUNT(DISTINCT h.id) as total_properties,
                SUM(ga.property_views) as total_views,
                SUM(ga.property_searches) as total_searches,
                AVG(ga.average_price) as avg_price,
                AVG(ga.demand_score) as avg_demand_score
            FROM geographic_analytics ga
            JOIN regions r ON ga.region_id = r.id
            LEFT JOIN houses h ON h.region_id = r.id
            WHERE ga.date >= DATE_SUB(CURRENT_DATE, INTERVAL 30 DAY)
            GROUP BY r.id, r.name
        """)
        metrics['regional_performance'] = cursor.fetchall()
        
        # Top performing regions
        cursor.execute("""
            SELECT 
                r.name as region_name,
                SUM(ga.property_views) as total_views,
                SUM(ga.property_searches) as total_searches,
                AVG(ga.demand_score) as avg_demand_score,
                COUNT(DISTINCT h.id) as property_count
            FROM geographic_analytics ga
            JOIN regions r ON ga.region_id = r.id
            LEFT JOIN houses h ON h.region_id = r.id
            WHERE ga.date >= DATE_SUB(CURRENT_DATE, INTERVAL 30 DAY)
            GROUP BY r.id, r.name
            ORDER BY total_views DESC
        """)
        metrics['top_regions'] = cursor.fetchall()
        
        # Regional demand trends
        cursor.execute("""
            SELECT 
                r.name as region_name,
                ga.date,
                ga.property_views,
                ga.property_searches,
                ga.demand_score
            FROM geographic_analytics ga
            JOIN regions r ON ga.region_id = r.id
            WHERE ga.date >= DATE_SUB(CURRENT_DATE, INTERVAL 30 DAY)
            ORDER BY r.name, ga.date
        """)
        metrics['regional_trends'] = cursor.fetchall()
        
        # Price analysis by region
        cursor.execute("""
            SELECT 
                r.name as region_name,
                AVG(h.price) as avg_price,
                MIN(h.price) as min_price,
                MAX(h.price) as max_price,
                COUNT(h.id) as property_count
            FROM houses h
            JOIN regions r ON h.region_id = r.id
            GROUP BY r.id, r.name
            ORDER BY avg_price DESC
        """)
        metrics['price_analysis'] = cursor.fetchall()
        
    except Exception as e:
        print(f"Error getting geographic analytics: {e}")
        metrics = {}
    finally:
        cursor.close()
        conn.close()
    
    return metrics

def get_search_analytics():
    """Get comprehensive search analytics"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    metrics = {}
    
    try:
        # Search summary
        cursor.execute("""
            SELECT 
                COUNT(*) as total_searches,
                COUNT(DISTINCT user_id) as unique_searchers,
                AVG(results_count) as avg_results_per_search
            FROM search_analytics 
            WHERE searched_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
        """)
        metrics['search_summary'] = cursor.fetchone()
        
        # Popular search terms
        cursor.execute("""
            SELECT 
                search_term,
                COUNT(*) as search_count,
                AVG(results_count) as avg_results
            FROM search_analytics 
            WHERE searched_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            AND search_term IS NOT NULL 
            AND search_term != ''
            GROUP BY search_term
            ORDER BY search_count DESC
            LIMIT 20
        """)
        metrics['popular_searches'] = cursor.fetchall()
        
        # Search trends over time
        cursor.execute("""
            SELECT 
                DATE(searched_at) as search_date,
                COUNT(*) as daily_searches,
                COUNT(DISTINCT user_id) as unique_searchers
            FROM search_analytics 
            WHERE searched_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            GROUP BY DATE(searched_at)
            ORDER BY search_date
        """)
        metrics['search_trends'] = cursor.fetchall()
        
        # Search performance by filters
        cursor.execute("""
            SELECT 
                JSON_EXTRACT(filters_applied, '$.property_type') as property_type_filter,
                JSON_EXTRACT(filters_applied, '$.region') as region_filter,
                COUNT(*) as filter_usage_count,
                AVG(results_count) as avg_results
            FROM search_analytics 
            WHERE searched_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
            AND filters_applied IS NOT NULL
            GROUP BY property_type_filter, region_filter
            ORDER BY filter_usage_count DESC
            LIMIT 15
        """)
        metrics['filter_usage'] = cursor.fetchall()
        
    except Exception as e:
        print(f"Error getting search analytics: {e}")
        metrics = {}
    finally:
        cursor.close()
        conn.close()
    
    return metrics

def get_all_advanced_metrics():
    """Get all advanced metrics in one call"""
    return {
        'revenue_analytics': get_revenue_analytics(),
        'user_engagement': get_user_engagement_metrics(),
        'property_performance': get_property_performance_metrics(),
        'geographic_analytics': get_geographic_analytics(),
        'search_analytics': get_search_analytics()
    }
