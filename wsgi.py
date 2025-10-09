"""
WSGI entry point for production deployment on Render
"""

import os
from dotenv import load_dotenv
from app import app

# Load environment variables
load_dotenv()

# This is the application object that WSGI servers will use
application = app

if __name__ == "__main__":
    # This is only used when running locally
    port = int(os.environ.get('PORT', 5002))
    debug = os.environ.get('FLASK_ENV') != 'production'
    app.run(host='0.0.0.0', port=port, debug=debug)