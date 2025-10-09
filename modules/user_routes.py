from flask import Blueprint, render_template, request, session, flash, redirect, url_for, jsonify
import json
import random
import logging
from modules.database import get_db_connection

user_bp = Blueprint('user', __name__)  # REMOVED: url_prefix='/user'

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@user_bp.route('/')
def index():
    """Main landing page"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Get ALL houses with region and neighborhood names - REMOVED availability filter
        cursor.execute("""
            SELECT h.*, r.name as region_name, n.name as neighborhood_name
            FROM houses h
            LEFT JOIN regions r ON h.region_id = r.id
            LEFT JOIN neighborhoods n ON h.neighborhood_id = n.id
            ORDER BY h.created_at DESC
        """)  # REMOVED: WHERE h.is_available = TRUE
        featured_houses = cursor.fetchall()

        # DEBUG: Print house count and details
        print(f"DEBUG: Fetched {len(featured_houses)} houses for landing page")
        for i, house in enumerate(featured_houses):
            print(f"House {i+1}: {house['title']} - Available: {house['is_available']}")

        # Parse image_paths for each house
        for house in featured_houses:
            if house['image_paths']:
                try:
                    if isinstance(house['image_paths'], str):
                        house['image_paths'] = json.loads(house['image_paths'].replace("'", '"'))
                except:
                    house['image_paths'] = [house['image_paths']] if house['image_paths'] else []
            else:
                house['image_paths'] = []

    except Exception as e:
        print(f"Error loading houses: {str(e)}")
        featured_houses = []
    finally:
        cursor.close()
        conn.close()

    return render_template('user/index.html', featured_houses=featured_houses)


@user_bp.route('/houses')
def houses():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Get filter parameters with enhanced handling
    region_filter = request.args.get('region', '')
    property_type_filter = request.args.get('property_type', '')
    min_price = request.args.get('min_price', '')
    max_price = request.args.get('max_price', '')
    search_filter = request.args.get('search', '')
    sort_filter = request.args.get('sort', 'newest')

    # Debug: Print received filters
    print(f"DEBUG - Filters received: region={region_filter}, property_type={property_type_filter}, min_price={min_price}, max_price={max_price}, search={search_filter}, sort={sort_filter}")

    # Build query with filters - ENHANCED with search and sort
    query = """
        SELECT h.*, r.name as region_name, n.name as neighborhood_name
        FROM houses h
        LEFT JOIN regions r ON h.region_id = r.id
        LEFT JOIN neighborhoods n ON h.neighborhood_id = n.id
        WHERE 1=1
    """
    params = []

    # Text search filter - NEW: Search by title or description
    if search_filter and search_filter != '':
        query += " AND (h.title LIKE %s OR h.description LIKE %s)"
        params.extend([f'%{search_filter}%', f'%{search_filter}%'])
        print(f"DEBUG - Applying search filter: {search_filter}")

    # Region filter - FIXED: Better handling
    if region_filter and region_filter.strip() and region_filter.isdigit():
        query += " AND h.region_id = %s"
        params.append(int(region_filter))  # Ensure it's integer
        print(f"DEBUG - Applying region filter: {region_filter}")

    # Property type filter - FIXED: Better handling
    if property_type_filter and property_type_filter != '':
        query += " AND h.property_type = %s"
        params.append(property_type_filter)
        print(f"DEBUG - Applying property type filter: {property_type_filter}")

    # Price filters - FIXED: Better validation
    if min_price and min_price.strip() and min_price.replace('.', '').isdigit():
        query += " AND h.price >= %s"
        params.append(float(min_price))
        print(f"DEBUG - Applying min price filter: {min_price}")

    if max_price and max_price.strip() and max_price.replace('.', '').isdigit():
        query += " AND h.price <= %s"
        params.append(float(max_price))
        print(f"DEBUG - Applying max price filter: {max_price}")

    # Sorting - NEW: Multiple sort options
    if sort_filter == 'price_low':
        query += " ORDER BY h.price ASC"
        print("DEBUG - Sorting by: Price Low to High")
    elif sort_filter == 'price_high':
        query += " ORDER BY h.price DESC"
        print("DEBUG - Sorting by: Price High to Low")
    elif sort_filter == 'name':
        query += " ORDER BY h.title ASC"
        print("DEBUG - Sorting by: Name A-Z")
    else:  # newest (default)
        query += " ORDER BY h.created_at DESC"
        print("DEBUG - Sorting by: Newest First")

    print(f"DEBUG - Final query: {query}")
    print(f"DEBUG - Query params: {params}")

    try:
        print(f"DEBUG - Executing query: {query}")
        print(f"DEBUG - With parameters: {params}")
        cursor.execute(query, params)
        houses = cursor.fetchall()
        print(f"DEBUG - Found {len(houses)} houses after filtering")
        
        # Debug: Print first few houses if any
        if houses:
            print(f"DEBUG - First house: {houses[0]['title'] if houses[0] else 'None'}")
        
    except Exception as e:
        print(f"ERROR - Query failed: {e}")
        print(f"ERROR - Query was: {query}")
        print(f"ERROR - Params were: {params}")
        
        # Fallback to all houses if query fails
        try:
            cursor.execute("""
                SELECT h.*, r.name as region_name, n.name as neighborhood_name
                FROM houses h
                LEFT JOIN regions r ON h.region_id = r.id
                LEFT JOIN neighborhoods n ON h.neighborhood_id = n.id
                ORDER BY h.created_at DESC
            """)
            houses = cursor.fetchall()
            print(f"DEBUG - Fallback query returned {len(houses)} houses")
        except Exception as fallback_error:
            print(f"ERROR - Fallback query also failed: {fallback_error}")
            houses = []

    # Parse image_paths for each house
    for house in houses:
        if house['image_paths']:
            try:
                if isinstance(house['image_paths'], str):
                    house['image_paths'] = json.loads(house['image_paths'].replace("'", '"'))
            except:
                house['image_paths'] = []
        else:
            house['image_paths'] = []

    # Track search if filters are applied
    try:
        from modules.analytics_tracking import track_search, update_user_engagement
        
        if any([region_filter, property_type_filter, min_price, max_price, search_filter]):
            track_search(
                user_id=session.get('user_id'),
                search_term=search_filter,
                filters_applied={
                    'region': region_filter,
                    'property_type': property_type_filter,
                    'min_price': min_price,
                    'max_price': max_price
                },
                results_count=len(houses),
                ip_address=request.remote_addr,
                session_id=session.get('session_id')
            )
            
            # Update user engagement
            if session.get('user_id'):
                update_user_engagement(session['user_id'], 'search')
    except Exception as e:
        print(f"Error tracking search: {e}")

    # Get all regions for filter dropdown
    cursor.execute("SELECT * FROM regions ORDER BY name")
    regions = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('user/houses.html',
                           houses=houses,
                           regions=regions,
                           current_region=region_filter,
                           current_property_type=property_type_filter,
                           current_min_price=min_price,
                           current_max_price=max_price,
                           current_search=search_filter,
                           current_sort=sort_filter)

@user_bp.route('/house/<int:house_id>')
def house_detail(house_id):
    from modules.analytics_tracking import track_property_view, update_user_engagement
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Get house details
    cursor.execute("""
        SELECT h.*, r.name as region_name, n.name as neighborhood_name
        FROM houses h
        LEFT JOIN regions r ON h.region_id = r.id
        LEFT JOIN neighborhoods n ON h.neighborhood_id = n.id
        WHERE h.id = %s
    """, (house_id,))
    house = cursor.fetchone()

    if not house:
        cursor.close()
        conn.close()
        return "House not found", 404

    # Parse image_paths
    if house['image_paths']:
        try:
            if isinstance(house['image_paths'], str):
                house['image_paths'] = json.loads(house['image_paths'].replace("'", '"'))
        except:
            house['image_paths'] = []
    else:
        house['image_paths'] = []

    # Track property view
    try:
        track_property_view(
            property_id=house_id,
            user_id=session.get('user_id'),
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            session_id=session.get('session_id')
        )
        
        # Update user engagement
        if session.get('user_id'):
            update_user_engagement(session['user_id'], 'property_view')
    except Exception as e:
        print(f"Error tracking property view: {e}")

    cursor.close()
    conn.close()

    return render_template('user/house_detail.html', house=house)

@user_bp.route('/tenant-dashboard')
def tenant_dashboard():
    """Tenant dashboard showing available houses and search functionality"""
    if not session.get('logged_in'):
        flash('Please login to access your dashboard.', 'error')
        return redirect(url_for('auth.login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get available houses for the tenant
        cursor.execute("""
            SELECT h.*, r.name as region_name, n.name as neighborhood_name
            FROM houses h
            LEFT JOIN regions r ON h.region_id = r.id
            LEFT JOIN neighborhoods n ON h.neighborhood_id = n.id
            WHERE h.is_available = TRUE
            ORDER BY h.created_at DESC
            LIMIT 12
        """)
        available_houses = cursor.fetchall()
        
        # Parse image_paths for each house
        for house in available_houses:
            if house['image_paths']:
                try:
                    if isinstance(house['image_paths'], str):
                        house['image_paths'] = json.loads(house['image_paths'].replace("'", '"'))
                except:
                    house['image_paths'] = [house['image_paths']] if house['image_paths'] else []
            else:
                house['image_paths'] = []
        
        # Get regions for search filter
        cursor.execute("SELECT * FROM regions ORDER BY name")
        regions = cursor.fetchall()
        
        # Get user's favorite houses if any
        cursor.execute("""
            SELECT h.* FROM houses h
            JOIN favorites f ON h.id = f.house_id
            WHERE f.user_id = %s AND h.is_available = TRUE
        """, (session['user_id'],))
        favorite_houses = cursor.fetchall()
        
        # Parse image_paths for favorites
        for house in favorite_houses:
            if house['image_paths']:
                try:
                    if isinstance(house['image_paths'], str):
                        house['image_paths'] = json.loads(house['image_paths'].replace("'", '"'))
                except:
                    house['image_paths'] = [house['image_paths']] if house['image_paths'] else []
            else:
                house['image_paths'] = []
                
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'error')
        available_houses = []
        regions = []
        favorite_houses = []
    finally:
        cursor.close()
        conn.close()
    
    return render_template('user/tenant_dashboard.html',
                         available_houses=available_houses,
                         regions=regions,
                         favorite_houses=favorite_houses)

@user_bp.route('/user-analytics')
def user_analytics():
    """User analytics dashboard for tenants"""
    if not session.get('logged_in'):
        flash('Please login to access your analytics.', 'error')
        return redirect(url_for('auth.login'))
    
    try:
        from modules.user_analytics import get_user_activity_analytics
        
        user_id = session['user_id']
        analytics = get_user_activity_analytics(user_id)
        
        return render_template('user/analytics_dashboard.html', 
                             analytics=analytics,
                             user_id=user_id)
        
    except Exception as e:
        flash(f'Error loading analytics: {str(e)}', 'error')
        return render_template('user/analytics_dashboard.html', 
                             analytics={},
                             user_id=session.get('user_id', 0))

@user_bp.route('/add-favorite/<int:property_id>', methods=['POST'])
def add_favorite(property_id):
    """Add property to favorites"""
    if not session.get('logged_in'):
        return {'success': False, 'message': 'Please login first'}
    
    try:
        from modules.user_analytics import add_to_favorites
        
        user_id = session['user_id']
        success = add_to_favorites(user_id, property_id)
        
        if success:
            return {'success': True, 'message': 'Added to favorites'}
        else:
            return {'success': False, 'message': 'Error adding to favorites'}
            
    except Exception as e:
        return {'success': False, 'message': str(e)}

@user_bp.route('/remove-favorite/<int:property_id>', methods=['POST'])
def remove_favorite(property_id):
    """Remove property from favorites"""
    if not session.get('logged_in'):
        return {'success': False, 'message': 'Please login first'}
    
    try:
        from modules.user_analytics import remove_from_favorites
        
        user_id = session['user_id']
        success = remove_from_favorites(user_id, property_id)
        
        if success:
            return {'success': True, 'message': 'Removed from favorites'}
        else:
            return {'success': False, 'message': 'Error removing from favorites'}
            
    except Exception as e:
        return {'success': False, 'message': str(e)}

@user_bp.route('/save-search', methods=['POST'])
def save_search():
    """Save user's search"""
    if not session.get('logged_in'):
        return {'success': False, 'message': 'Please login first'}
    
    try:
        from modules.user_analytics import save_search
        
        user_id = session['user_id']
        search_name = request.json.get('search_name')
        search_term = request.json.get('search_term')
        filters_applied = request.json.get('filters_applied')
        
        success = save_search(user_id, search_name, search_term, filters_applied)
        
        if success:
            return {'success': True, 'message': 'Search saved successfully'}
        else:
            return {'success': False, 'message': 'Error saving search'}
            
    except Exception as e:
        return {'success': False, 'message': str(e)}

# Property type mapping
PROPERTY_TYPE_MAPPING = {
    'single_room': ['single room', 'single', 'room', 'one room'],
    'chamber_hall': ['chamber', 'chamber hall', 'chamber and hall', 'hall'],
    '2_bedroom': ['2 bedroom', '2-bedroom', 'two bedroom', '2 bed'],
    '3_bedroom': ['3 bedroom', '3-bedroom', 'three bedroom', '3 bed'],
    'self_contained': ['self contained', 'self-contained', 'self contain', 'selfcontained'],
    'store': ['store', 'shop', 'commercial', 'business', 'retail'],
    'apartment': ['apartment', 'flat', 'unit']
}

# Region mapping
REGION_MAPPING = {
    'accra': ['accra', 'greater accra'],
    'kumasi': ['kumasi', 'ashanti'],
    'takoradi': ['takoradi', 'western'],
    'cape coast': ['cape coast', 'central'],
    'tema': ['tema'],
    'eastern': ['eastern', 'koforidua'],
    'volta': ['volta', 'ho'],
    'northern': ['northern', 'tamale']
}

def detect_property_type(user_message):
    """Detect property type from user message with fuzzy matching"""
    user_message = user_message.lower()

    for db_type, keywords in PROPERTY_TYPE_MAPPING.items():
        for keyword in keywords:
            if keyword in user_message:
                return db_type
    return None

def detect_region(user_message):
    """Detect region from user message"""
    user_message = user_message.lower()

    for region, keywords in REGION_MAPPING.items():
        for keyword in keywords:
            if keyword in user_message:
                return region
    return None

def detect_budget(user_message):
    """Extract budget range from user message"""
    user_message = user_message.lower()

    if 'under 1000' in user_message or 'below 1000' in user_message or 'less than 1000' in user_message:
        return 1000
    elif 'under 5000' in user_message or 'below 5000' in user_message:
        return 5000
    elif 'under 10000' in user_message or 'below 10000' in user_message:
        return 10000

    import re
    price_matches = re.findall(r'(\d+)\s*(?:ghs?|cedis?)?', user_message)
    if price_matches:
        return int(price_matches[0])

    return None

def get_property_type_display_name(property_type):
    """Convert database property_type to readable format"""
    return property_type.replace('_', ' ').title()

def execute_safe_query(cursor, query, params=None):
    """Execute query with proper error handling"""
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return cursor.fetchall()
    except Exception as e:
        logger.error(f"Query failed: {e}")
        return []

@user_bp.route('/chatbot', methods=['POST'])
def chatbot():
    user_message = request.json.get('message', '').strip()
    response = ""
    properties = []

    if not user_message:
        return jsonify({'response': "Please type a message so I can help you! 😊", 'properties': []})

    logger.info(f"Chatbot received: {user_message}")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        user_message_lower = user_message.lower()

        # === GREETINGS & BASIC INTERACTION ===
        if any(word in user_message_lower for word in ['hello', 'hi', 'hey', 'hola']):
            greetings = [
                "👋 Hello! I'm your GhanaRentals assistant! I can help you find properties across Ghana.",
                "🏡 Hi there! Ready to find your perfect rental? I'm here to help!",
                "😊 Hey! Welcome to GhanaRentals! What can I help you find today?"
            ]
            response = random.choice(greetings)

        # === PROPERTY SEARCH QUERIES ===
        elif any(word in user_message_lower for word in [
            'house', 'property', 'rent', 'room', 'apartment', 'looking for',
            'need a', 'show me', 'find', 'want', 'store', 'shop', 'commercial',
            'bedroom', 'self contained', 'chamber', 'single'
        ]):
            property_type = detect_property_type(user_message_lower)
            region = detect_region(user_message_lower)
            budget = detect_budget(user_message_lower)

            logger.info(f"Detected - Type: {property_type}, Region: {region}, Budget: {budget}")

            query = """
                SELECT h.*, r.name as region_name, n.name as neighborhood_name 
                FROM houses h 
                LEFT JOIN regions r ON h.region_id = r.id 
                LEFT JOIN neighborhoods n ON h.neighborhood_id = n.id 
                WHERE 1=1
            """
            params = []

            if region:
                if region == 'accra':
                    query += " AND r.name LIKE %s"
                    params.append('%Accra%')
                elif region == 'kumasi':
                    query += " AND r.name LIKE %s"
                    params.append('%Ashanti%')

            if property_type:
                if property_type == 'apartment':
                    query += " AND h.property_type IN (%s, %s, %s)"
                    params.extend(['2_bedroom', '3_bedroom', 'self_contained'])
                else:
                    query += " AND h.property_type = %s"
                    params.append(property_type)

            if budget:
                query += " AND h.price <= %s"
                params.append(budget)

            query += " ORDER BY h.created_at DESC LIMIT 5"

            properties = execute_safe_query(cursor, query, params)

            if properties:
                response_parts = []

                if region:
                    response_parts.append(f"🏙️ Found in {region.title()}")
                else:
                    response_parts.append("🏠 Found")

                if property_type:
                    display_type = get_property_type_display_name(property_type)
                    response_parts.append(f"{display_type} properties")
                else:
                    response_parts.append("properties")

                if budget:
                    response_parts.append(f"under GHS {budget}")

                response = " ".join(response_parts) + ": "

                for i, prop in enumerate(properties[:3]):
                    prop_type_display = get_property_type_display_name(prop['property_type'])
                    response += f"{prop['title']} ({prop_type_display}) - GHS {prop['price']}. "

                if len(properties) > 3:
                    response += f" Plus {len(properties) - 3} more on our website!"

            else:
                suggestions = []
                if property_type:
                    suggestions.append(f"try different {get_property_type_display_name(property_type)} options")
                if region:
                    suggestions.append(f"try different regions besides {region}")
                if budget:
                    suggestions.append(f"adjust your budget from GHS {budget}")

                if suggestions:
                    response = f"🔍 No properties found. You could {', '.join(suggestions)}."
                else:
                    response = "🔍 No properties found with those criteria. Try different search terms!"

        # === AFFIRMATIVE RESPONSES ===
        elif any(word in user_message_lower for word in ['yes', 'yeah', 'sure', 'ok', 'show me', 'please']):
            properties = execute_safe_query(cursor, """
                SELECT h.*, r.name as region_name, n.name as neighborhood_name 
                FROM houses h 
                LEFT JOIN regions r ON h.region_id = r.id 
                LEFT JOIN neighborhoods n ON h.neighborhood_id = n.id 
                ORDER BY h.created_at DESC LIMIT 6
            """)

            if properties:
                response = "🏡 Here are available properties: "
                for prop in properties[:4]:
                    prop_type = get_property_type_display_name(prop['property_type'])
                    response += f"{prop['title']} in {prop['region_name']} ({prop_type}) - GHS {prop['price']}. "
                response += f"Visit our '{url_for('user.houses')}' page for more details!"
            else:
                response = "📝 No properties listed yet. Check back soon or landlords can add properties!"

        # === HELP & GUIDANCE ===
        elif any(word in user_message_lower for word in ['help', 'what can you do', 'how does this work']):
            response = """ℹ️ I can help you:
• Find properties by type: single rooms, chamber & hall, 2/3-bedroom, self-contained, stores
• Search by location: Accra, Kumasi, Takoradi, etc.
• Filter by budget: "under GHS 1000", "budget 5000"
• Show available properties
Just tell me what you're looking for! 🏠"""

        # === CONTACT QUERIES ===
        elif any(word in user_message_lower for word in ['contact', 'landlord', 'owner', 'phone', 'email']):
            response = "📞 To contact landlords, please visit the property details page where you'll find direct contact information for quick responses!"

        # === THANK YOU ===
        elif any(word in user_message_lower for word in ['thank', 'thanks', 'appreciate']):
            responses = [
                "😊 You're very welcome! Happy to help you find your dream home!",
                "🌟 My pleasure! Don't hesitate to ask if you need more help!",
                "🏡 Anytime! Wishing you the best in your property search!"
            ]
            response = random.choice(responses)

        # === DEFAULT RESPONSE ===
        else:
            responses = [
                "🤔 I'm here to help with rental properties in Ghana. Try asking about property types, locations, or your budget!",
                "🎯 Let me help you find your perfect home! Ask me about single rooms, apartments, stores, or specific locations!",
                "🔍 I specialize in Ghana rentals! Tell me what you need: property type, location, or budget range."
            ]
            response = random.choice(responses)

    except Exception as e:
        logger.error(f"Chatbot error: {str(e)}")
        response = "😅 I'm having some technical difficulties right now. Please try our 'Browse Houses' page or check back in a few minutes!"

    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass

    logger.info(f"Chatbot response: {response}")
    return jsonify({
        'response': response,
        'properties': properties[:3]
    })
