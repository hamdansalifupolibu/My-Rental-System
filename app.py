from flask import Flask, render_template, redirect, url_for, session, flash, request, jsonify
import traceback
import os
from dotenv import load_dotenv
from modules.database import get_db_connection

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configuration based on environment
config_name = os.environ.get('FLASK_ENV', 'development')
if config_name == 'production':
    from config_production import ProductionConfig
    app.config.from_object(ProductionConfig)
else:
    from config_production import DevelopmentConfig
    app.config.from_object(DevelopmentConfig)

# Legacy config mapping for existing code
app.config['MYSQL_HOST'] = app.config['DB_HOST']
app.config['MYSQL_USER'] = app.config['DB_USER']
app.config['MYSQL_PASSWORD'] = app.config['DB_PASSWORD']
app.config['MYSQL_DB'] = app.config['DB_NAME']

# Import and register blueprints
try:
    from modules.auth import auth_bp
    from modules.admin_routes import admin_bp
    from modules.user_routes import user_bp
    from modules.report_routes import report_bp  # ADD THIS IMPORT

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(report_bp)  # ADD THIS REGISTRATION
    print("✅ Blueprints registered successfully")
except Exception as e:
    print(f"❌ Error registering blueprints: {e}")
    traceback.print_exc()

# Remove the conflicting home route from app.py since it's handled by user_routes.py
# The user_bp already has a route for '/' that properly fetches houses

# Remove these conflicting routes since they're handled by blueprints:
# @app.route('/')
# @app.route('/houses')
# @app.route('/house/<int:house_id>')

# Auth routes (direct routes to match HTML) - KEEP THESE
@app.route('/login', methods=['GET', 'POST'])
def login():
    from modules.auth import login as auth_login
    return auth_login()


@app.route('/register', methods=['GET', 'POST'])
def register():
    from modules.auth import register as auth_register
    return auth_register()


@app.route('/logout')
def logout():
    from modules.auth import logout as auth_logout
    return auth_logout()


@app.route('/profile')
def profile():
    from modules.auth import profile as auth_profile
    return auth_profile()


# Report routes (direct routes to match HTML) - ADD THESE NEW ROUTES
@app.route('/report-issue', methods=['GET', 'POST'])
def report_issue():
    from modules.report_routes import report_issue as report_issue_route
    return report_issue_route()


@app.route('/my-reports')
def my_reports():
    from modules.report_routes import my_reports as my_reports_route
    return my_reports_route()


# Chatbot endpoint - KEEP THIS
@app.route('/chatbot', methods=['POST'])
def chatbot():
    try:
        data = request.get_json()
        user_message = data.get('message', '').lower()

        # Simple chatbot responses
        responses = {
            'hello': '👋 Hello! Welcome to GhanaRentals! How can I help you find your perfect home?',
            'hi': '👋 Hi there! Ready to explore amazing rental properties in Ghana?',
            'help': '🤗 I can help you: 1) Find houses by region 2) Search by price range 3) Filter by property type 4) Answer questions about rentals',
            'price': '💰 Our properties range from GHS 200 to GHS 5000 per month. Use the search filters to find within your budget!',
            'region': '📍 We have properties in all 16 regions of Ghana! Where are you looking to rent?',
            'type': '🏠 We offer: Single rooms, Apartments, Stores, Halls, and more! What type are you interested in?',
            'contact': '📞 You can contact landlords directly through property details. For platform support, email: support@ghanarentals.com',
            'thank': 'You\'re welcome! 😊 Happy house hunting!',
            'bye': 'Goodbye! 👋 Hope you find your dream home soon!'
        }

        # Find matching response
        response = "🏡 I'm here to help with your rental search in Ghana! You can ask me about: prices, regions, property types, or how to contact landlords."

        for key in responses:
            if key in user_message:
                response = responses[key]
                break

        return jsonify({'response': response})

    except Exception as e:
        print(f"Chatbot error: {e}")
        return jsonify({'response': "😅 Sorry, I'm having trouble responding. Please try again!"})


@app.errorhandler(500)
def internal_error(error):
    return f"<h1>500 Error</h1><pre>{traceback.format_exc()}</pre>", 500


@app.errorhandler(404)
def not_found(error):
    return "<h1>404 - Page not found</h1>", 404

# Tenant dashboard is handled by user_routes.py blueprint

if __name__ == '__main__':
    # Get port from environment variable (for Render) or use default
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    

    app.run(host='0.0.0.0', port=5000, debug=True)
