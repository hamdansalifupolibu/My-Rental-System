from modules.database import get_db_connection
from datetime import datetime, timedelta


def get_user_metrics():
    """Get comprehensive user metrics"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    metrics = {}

    try:
        # Total users by role
        cursor.execute("SELECT role, COUNT(*) as count FROM users GROUP BY role")
        role_counts = cursor.fetchall()
        metrics['role_counts'] = {item['role']: item['count'] for item in role_counts}

        # Total users
        cursor.execute("SELECT COUNT(*) as total FROM users")
        metrics['total_users'] = cursor.fetchone()['total']

        # New users this month
        cursor.execute("""
            SELECT COUNT(*) as count FROM users 
            WHERE MONTH(created_at) = MONTH(CURRENT_DATE) 
            AND YEAR(created_at) = YEAR(CURRENT_DATE)
        """)
        metrics['new_users_this_month'] = cursor.fetchone()['count']

        # Active users (logged in last 30 days)
        cursor.execute("""
            SELECT COUNT(*) as count FROM users 
            WHERE last_login >= DATE_SUB(NOW(), INTERVAL 30 DAY)
        """)
        metrics['active_users'] = cursor.fetchone()['count']

        # Users created in last 7 days (for chart)
        cursor.execute("""
            SELECT DATE(created_at) as date, COUNT(*) as count 
            FROM users 
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            GROUP BY DATE(created_at) 
            ORDER BY date
        """)
        metrics['user_growth'] = cursor.fetchall()

    except Exception as e:
        print(f"Error getting user metrics: {e}")
        metrics = {}
    finally:
        cursor.close()
        conn.close()

    return metrics


def get_property_metrics():
    """Get comprehensive property metrics"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    metrics = {}

    try:
        # Total properties
        cursor.execute("SELECT COUNT(*) as total FROM houses")
        metrics['total_properties'] = cursor.fetchone()['total']

        # Properties by type
        cursor.execute("SELECT property_type, COUNT(*) as count FROM houses GROUP BY property_type")
        metrics['properties_by_type'] = cursor.fetchall()

        # Occupancy rate
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(is_occupied) as occupied,
                ROUND((SUM(is_occupied) / COUNT(*)) * 100, 2) as occupancy_rate
            FROM houses
        """)
        occupancy = cursor.fetchone()
        metrics['occupancy'] = occupancy

        # Available vs occupied
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN is_occupied = 1 THEN 1 ELSE 0 END) as occupied,
                SUM(CASE WHEN is_occupied = 0 THEN 1 ELSE 0 END) as available
            FROM houses
        """)
        metrics['availability'] = cursor.fetchone()

        # Properties by completion status
        cursor.execute("SELECT completion_status, COUNT(*) as count FROM houses GROUP BY completion_status")
        metrics['completion_status'] = cursor.fetchall()

        # Top viewed properties
        cursor.execute("SELECT id, title, views_count FROM houses ORDER BY views_count DESC LIMIT 5")
        metrics['top_viewed'] = cursor.fetchall()

        # New listings this month
        cursor.execute("""
            SELECT COUNT(*) as count FROM houses 
            WHERE MONTH(created_at) = MONTH(CURRENT_DATE) 
            AND YEAR(created_at) = YEAR(CURRENT_DATE)
        """)
        metrics['new_listings'] = cursor.fetchone()['count']

    except Exception as e:
        print(f"Error getting property metrics: {e}")
        metrics = {}
    finally:
        cursor.close()
        conn.close()

    return metrics


def get_report_metrics():
    """Get comprehensive report metrics"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    metrics = {}

    try:
        # Total reports
        cursor.execute("SELECT COUNT(*) as total FROM reports")
        metrics['total_reports'] = cursor.fetchone()['total']

        # Reports by status
        cursor.execute("SELECT status, COUNT(*) as count FROM reports GROUP BY status")
        metrics['reports_by_status'] = cursor.fetchall()

        # Reports by type
        cursor.execute("SELECT report_type, COUNT(*) as count FROM reports GROUP BY report_type")
        metrics['reports_by_type'] = cursor.fetchall()

        # Reports by priority
        cursor.execute("SELECT priority, COUNT(*) as count FROM reports GROUP BY priority")
        metrics['reports_by_priority'] = cursor.fetchall()

        # High priority pending reports
        cursor.execute("""
            SELECT COUNT(*) as count FROM reports 
            WHERE priority IN ('high', 'urgent') AND status = 'pending'
        """)
        metrics['critical_pending'] = cursor.fetchone()['count']

        # Recent reports (last 7 days)
        cursor.execute("""
            SELECT DATE(created_at) as date, COUNT(*) as count 
            FROM reports 
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            GROUP BY DATE(created_at) 
            ORDER BY date
        """)
        metrics['recent_reports'] = cursor.fetchall()

    except Exception as e:
        print(f"Error getting report metrics: {e}")
        metrics = {}
    finally:
        cursor.close()
        conn.close()

    return metrics


def get_all_metrics():
    """Get all metrics in one call"""
    # Import advanced metrics
    try:
        from modules.advanced_metrics import get_all_advanced_metrics
        advanced_metrics = get_all_advanced_metrics()
    except ImportError:
        advanced_metrics = {}
    
    return {
        'user_metrics': get_user_metrics(),
        'property_metrics': get_property_metrics(),
        'report_metrics': get_report_metrics(),
        'advanced_metrics': advanced_metrics
    }