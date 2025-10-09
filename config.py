import os


class Config:
    # Use the key you just generated
    SECRET_KEY = 'mysql+pymysql://user:pass@localhost/rental_service'  # ← PASTE YOUR KEY HERE

    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = ''
    MYSQL_DB = 'rental_service'
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024