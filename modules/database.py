import mysql.connector
import os
from flask import current_app
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_db_connection():
    """Get database connection with environment-based configuration"""
    try:
        # Use environment variables if available, otherwise fall back to app config
        host = os.environ.get('DB_HOST') or current_app.config.get('MYSQL_HOST', 'localhost')
        user = os.environ.get('DB_USER') or current_app.config.get('MYSQL_USER', 'root')
        password = os.environ.get('DB_PASSWORD') or current_app.config.get('MYSQL_PASSWORD', '')
        database = os.environ.get('DB_NAME') or current_app.config.get('MYSQL_DB', 'rental_service')
        port = int(os.environ.get('DB_PORT', current_app.config.get('MYSQL_PORT', 3306)))
        
        conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            port=port,
            autocommit=True,
            charset='utf8mb4',
            use_unicode=True
        )
        return conn
    except mysql.connector.Error as e:
        print(f"Database connection error: {e}")
        raise e
    except Exception as e:
        print(f"Unexpected database error: {e}")
        raise e