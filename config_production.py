"""
Production Configuration for GhanaRentals
Optimized for Render hosting platform
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ProductionConfig:
    """Production configuration settings"""
    
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-super-secret-production-key-change-this'
    DEBUG = False
    TESTING = False
    
    # Database Configuration
    DB_HOST = os.environ.get('DB_HOST') or 'localhost'
    DB_USER = os.environ.get('DB_USER') or 'root'
    DB_PASSWORD = os.environ.get('DB_PASSWORD') or ''
    DB_NAME = os.environ.get('DB_NAME') or 'ghana_rentals'
    DB_PORT = int(os.environ.get('DB_PORT', 3306))
    
    # File Upload Configuration
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    
    # Security Configuration
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours
    
    # CORS Configuration
    CORS_ORIGINS = [
        "https://ghana-rentals.onrender.com",
        "https://www.ghana-rentals.onrender.com",
        "https://ghana-rentals.vercel.app",  # If using Vercel for frontend
    ]
    
    # Email Configuration (for notifications)
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    
    # Logging Configuration
    LOG_LEVEL = 'INFO'
    LOG_FILE = 'logs/app.log'
    
    # Performance Configuration
    JSON_SORT_KEYS = False
    JSONIFY_PRETTYPRINT_REGULAR = False
    
    # Cache Configuration (for future implementation)
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300
    
    # Rate Limiting (for future implementation)
    RATELIMIT_STORAGE_URL = 'memory://'
    RATELIMIT_DEFAULT = "100 per hour"
    
    @staticmethod
    def init_app(app):
        """Initialize application with production settings"""
        import logging
        from logging.handlers import RotatingFileHandler
        
        # Create logs directory if it doesn't exist
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        # Configure logging
        if not app.debug and not app.testing:
            file_handler = RotatingFileHandler(
                ProductionConfig.LOG_FILE, 
                maxBytes=10240000, 
                backupCount=10
            )
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
            ))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
            app.logger.setLevel(logging.INFO)
            app.logger.info('GhanaRentals startup')

class DevelopmentConfig:
    """Development configuration settings"""
    
    SECRET_KEY = 'dev-secret-key-change-in-production'
    DEBUG = True
    TESTING = False
    
    # Database Configuration
    DB_HOST = 'localhost'
    DB_USER = 'root'
    DB_PASSWORD = ''
    DB_NAME = 'ghana_rentals'
    DB_PORT = 3306
    
    # File Upload Configuration
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    
    # Security Configuration
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 86400

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
