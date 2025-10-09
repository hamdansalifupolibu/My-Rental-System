from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from modules.database import get_db_connection
import os
import uuid
import json
from werkzeug.utils import secure_filename
from functools import wraps

admin_bp = Blueprint('admin', __name__)

# Image upload configuration
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

def admin_required(f):
    """Decorator to require admin OR landlord role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in') or session.get('role') not in ['admin', 'landlord']:
            flash('Please login as admin or landlord to access this page.', 'error')
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

def admin_only(f):
    """Decorator to require admin role only"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in') or session.get('role') != 'admin':
            flash('Admin access required for this page.', 'error')
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

def landlord_only(f):
    """Decorator to require landlord role only"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in') or session.get('role') != 'landlord':
            flash('Landlord access required for this page.', 'error')
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_files(files, house_id):
    """Save uploaded files and return their paths"""
    uploaded_paths = []

    # Create house-specific folder
    upload_folder = 'static/uploads'
    house_folder = os.path.join(upload_folder, f'house_{house_id}')
    if not os.path.exists(house_folder):
        os.makedirs(house_folder)

    for file in files:
        if file and file.filename != '' and allowed_file(file.filename):
            # Generate unique filename
            file_ext = file.filename.rsplit('.', 1)[1].lower()
            unique_filename = f"{uuid.uuid4().hex}.{file_ext}"
            file_path = os.path.join(house_folder, unique_filename)

            # Save file
            file.save(file_path)

            # Store relative path for database
            relative_path = f"house_{house_id}/{unique_filename}"
            uploaded_paths.append(relative_path)

    return uploaded_paths


@admin_bp.route('/admin/dashboard')
@admin_only
def dashboard():
    """Admin-only dashboard with metrics"""
    from modules.metrics import get_all_metrics

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Get basic stats (your existing code)
        cursor.execute("SELECT COUNT(*) as total_users FROM users")
        total_users = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) as total_houses FROM houses")
        total_houses = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) as available_houses FROM houses WHERE is_available = TRUE")
        available_houses = cursor.fetchone()[0]

        # Get recent users
        cursor.execute("SELECT * FROM users ORDER BY created_at DESC LIMIT 5")
        recent_users = cursor.fetchall()

        # Get recent houses
        cursor.execute("SELECT * FROM houses ORDER BY created_at DESC LIMIT 5")
        recent_houses = cursor.fetchall()

        # Get metrics data
        metrics = get_all_metrics()

    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'error')
        total_users = total_houses = available_houses = 0
        recent_users = recent_houses = []
        metrics = {}
    finally:
        cursor.close()
        conn.close()

    return render_template('admin/dashboard.html',
                           total_users=total_users,
                           total_houses=total_houses,
                           available_houses=available_houses,
                           recent_users=recent_users,
                           recent_houses=recent_houses,
                           metrics=metrics)



@admin_bp.route('/admin/landlord-dashboard')
@landlord_only
def landlord_dashboard():
    """Landlord-only dashboard"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Get only the landlord's properties
    cursor.execute("""
        SELECT h.*, r.name as region_name, n.name as neighborhood_name
        FROM houses h
        LEFT JOIN regions r ON h.region_id = r.id
        LEFT JOIN neighborhoods n ON h.neighborhood_id = n.id
        WHERE h.created_by = %s
        ORDER BY h.created_at DESC
    """, (session['user_id'],))

    properties = cursor.fetchall()

    # Parse image_paths for each property
    for prop in properties:
        if prop['image_paths']:
            try:
                if isinstance(prop['image_paths'], str):
                    prop['image_paths'] = json.loads(prop['image_paths'].replace("'", '"'))
            except:
                prop['image_paths'] = [prop['image_paths']] if prop['image_paths'] else []
        else:
            prop['image_paths'] = []

    cursor.close()
    conn.close()

    return render_template('landlord/dashboard.html', properties=properties)

@admin_bp.route('/admin/landlord-revenue')
@landlord_only
def landlord_revenue_analytics():
    """Landlord revenue analytics dashboard"""
    try:
        from modules.landlord_analytics import get_landlord_revenue_metrics
        
        # Get landlord's revenue metrics
        landlord_id = session['user_id']
        revenue_metrics = get_landlord_revenue_metrics(landlord_id)
        
        return render_template('landlord/revenue_analytics.html', 
                             metrics=revenue_metrics,
                             landlord_id=landlord_id)
        
    except Exception as e:
        flash(f'Error loading revenue analytics: {str(e)}', 'error')
        return render_template('landlord/revenue_analytics.html', 
                             metrics={},
                             landlord_id=session.get('user_id', 0))

@admin_bp.route('/admin/landlord-property-analytics/<int:property_id>')
@landlord_only
def landlord_property_analytics(property_id):
    """Detailed analytics for a specific property"""
    try:
        from modules.landlord_analytics import get_landlord_property_analytics
        
        landlord_id = session['user_id']
        property_analytics = get_landlord_property_analytics(landlord_id, property_id)
        
        if not property_analytics:
            flash('Property not found or access denied', 'error')
            return redirect(url_for('admin_routes.landlord_dashboard'))
        
        return render_template('landlord/property_analytics.html', 
                             analytics=property_analytics)
        
    except Exception as e:
        flash(f'Error loading property analytics: {str(e)}', 'error')
        return redirect(url_for('admin_routes.landlord_dashboard'))

@admin_bp.route('/admin/add-house', methods=['GET', 'POST'])
@admin_only
def add_house():
    """Admin-only: Add house (full access)"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)  # CHANGED: Add dictionary=True

    # Get regions and neighborhoods for dropdowns
    cursor.execute("SELECT * FROM regions")
    regions = cursor.fetchall()

    cursor.execute("SELECT * FROM neighborhoods")
    neighborhoods = cursor.fetchall()

    if request.method == 'POST':
        try:
            # Get form data
            title = request.form['title']
            description = request.form['description']
            region_id = request.form.get('region_id')
            neighborhood_id = request.form.get('neighborhood_id')
            exact_location = request.form['exact_location']
            property_type = request.form['property_type']
            completion_status = request.form['completion_status']
            months_left = request.form.get('months_left') or None
            price = request.form['price']
            is_featured = 'is_featured' in request.form

            # Get contact information
            contact_name = request.form.get('contact_name')
            contact_phone = request.form.get('contact_phone')
            contact_email = request.form.get('contact_email')

            # Insert house into database
            cursor.execute("""
                INSERT INTO houses 
                (title, description, region_id, neighborhood_id, exact_location, 
                 property_type, completion_status, months_left, price, created_by, is_featured,
                 contact_name, contact_phone, contact_email)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (title, description, region_id, neighborhood_id, exact_location,
                  property_type, completion_status, months_left, price, session['user_id'], is_featured,
                  contact_name, contact_phone, contact_email))

            house_id = cursor.lastrowid

            # Handle image uploads
            image_paths = []
            if 'images' in request.files:
                files = request.files.getlist('images')
                image_paths = save_uploaded_files(files, house_id)

            # If no images uploaded, use placeholder
            if not image_paths:
                image_paths = ['house_placeholder.jpg']

            # Update house with image paths
            cursor.execute("UPDATE houses SET image_paths = %s WHERE id = %s",
                          (json.dumps(image_paths), house_id))

            conn.commit()
            flash(f'House added successfully with {len(image_paths)} images!', 'success')
            return redirect('/admin/manage-houses')

        except Exception as e:
            conn.rollback()
            flash(f'Error adding house: {str(e)}', 'error')
        finally:
            cursor.close()
            conn.close()

    else:
        cursor.close()
        conn.close()

    return render_template('admin/add_house.html',
                           regions=regions,
                           neighborhoods=neighborhoods)

@admin_bp.route('/admin/landlord/add-property', methods=['GET', 'POST'])
@landlord_only
def landlord_add_property():
    """Landlord-only: Add property (restricted access)"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)  # CHANGED: Add dictionary=True

    # Get regions and neighborhoods for dropdowns
    cursor.execute("SELECT * FROM regions")
    regions = cursor.fetchall()

    cursor.execute("SELECT * FROM neighborhoods")
    neighborhoods = cursor.fetchall()

    if request.method == 'POST':
        try:
            # Get form data
            title = request.form['title']
            description = request.form['description']
            region_id = request.form.get('region_id')
            neighborhood_id = request.form.get('neighborhood_id')
            exact_location = request.form['exact_location']
            property_type = request.form['property_type']
            completion_status = request.form['completion_status']
            months_left = request.form.get('months_left') or None
            price = request.form['price']

            # Landlords cannot feature properties
            is_featured = False

            # Get contact information
            contact_name = request.form.get('contact_name')
            contact_phone = request.form.get('contact_phone')
            contact_email = request.form.get('contact_email')

            # Insert house into database
            cursor.execute("""
                INSERT INTO houses 
                (title, description, region_id, neighborhood_id, exact_location, 
                 property_type, completion_status, months_left, price, created_by, is_featured,
                 contact_name, contact_phone, contact_email)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (title, description, region_id, neighborhood_id, exact_location,
                  property_type, completion_status, months_left, price, session['user_id'], is_featured,
                  contact_name, contact_phone, contact_email))

            house_id = cursor.lastrowid

            # Handle image uploads
            image_paths = []
            if 'images' in request.files:
                files = request.files.getlist('images')
                image_paths = save_uploaded_files(files, house_id)

            # If no images uploaded, use placeholder
            if not image_paths:
                image_paths = ['house_placeholder.jpg']

            # Update house with image paths
            cursor.execute("UPDATE houses SET image_paths = %s WHERE id = %s",
                          (json.dumps(image_paths), house_id))

            conn.commit()
            flash('Property added successfully!', 'success')
            return redirect('/admin/landlord-dashboard')

        except Exception as e:
            conn.rollback()
            flash(f'Error adding property: {str(e)}', 'error')
        finally:
            cursor.close()
            conn.close()

    else:
        cursor.close()
        conn.close()

    return render_template('landlord/add_property.html',
                           regions=regions,
                           neighborhoods=neighborhoods)

@admin_bp.route('/admin/landlord/edit-property/<int:property_id>', methods=['GET', 'POST'])
@landlord_only
def landlord_edit_property(property_id):
    """Landlord-only: Edit property (only their own)"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)  # CHANGED: Add dictionary=True

    # Verify the property belongs to this landlord
    cursor.execute("SELECT * FROM houses WHERE id = %s AND created_by = %s",
                   (property_id, session['user_id']))
    property_data = cursor.fetchone()  # Now this returns a dictionary

    if not property_data:
        flash('Property not found or access denied.', 'error')
        return redirect('/admin/landlord-dashboard')

    # Get regions and neighborhoods for dropdowns
    cursor.execute("SELECT * FROM regions")
    regions = cursor.fetchall()

    cursor.execute("SELECT * FROM neighborhoods")
    neighborhoods = cursor.fetchall()

    if request.method == 'POST':
        try:
            # Get form data
            title = request.form['title']
            description = request.form['description']
            region_id = request.form.get('region_id')
            neighborhood_id = request.form.get('neighborhood_id')
            exact_location = request.form['exact_location']
            property_type = request.form['property_type']
            completion_status = request.form['completion_status']
            months_left = request.form.get('months_left') or None
            price = request.form['price']

            # Landlords cannot change featured status
            is_featured = property_data['is_featured']  # CHANGED: Direct access

            # Get contact information
            contact_name = request.form.get('contact_name')
            contact_phone = request.form.get('contact_phone')
            contact_email = request.form.get('contact_email')

            # Get current image paths
            current_images = []
            if property_data['image_paths']:
                try:
                    if isinstance(property_data['image_paths'], str):
                        current_images = json.loads(property_data['image_paths'].replace("'", '"'))
                except:
                    current_images = [property_data['image_paths']] if property_data['image_paths'] else []

            # Handle image deletions
            delete_images = request.form.getlist('delete_images')
            updated_images = [img for img in current_images if img not in delete_images]

            # Handle new image uploads
            if 'images' in request.files:
                files = request.files.getlist('images')
                new_images = save_uploaded_files(files, property_id)
                updated_images.extend(new_images)

            # If no images left, use placeholder
            if not updated_images:
                updated_images = ['house_placeholder.jpg']

            # Update property in database
            cursor.execute("""
                UPDATE houses 
                SET title = %s, description = %s, region_id = %s, neighborhood_id = %s,
                    exact_location = %s, property_type = %s, completion_status = %s,
                    months_left = %s, price = %s, is_featured = %s, 
                    image_paths = %s, updated_at = CURRENT_TIMESTAMP,
                    contact_name = %s, contact_phone = %s, contact_email = %s
                WHERE id = %s AND created_by = %s
            """, (title, description, region_id, neighborhood_id, exact_location,
                  property_type, completion_status, months_left, price, is_featured,
                  json.dumps(updated_images), contact_name, contact_phone, contact_email,
                  property_id, session['user_id']))

            conn.commit()
            flash('Property updated successfully!', 'success')
            return redirect('/admin/landlord-dashboard')

        except Exception as e:
            conn.rollback()
            flash(f'Error updating property: {str(e)}', 'error')
        finally:
            cursor.close()
            conn.close()

    else:
        # GET request - load existing property data
        try:
            # Parse image_paths if it's a string
            if property_data['image_paths']:
                try:
                    if isinstance(property_data['image_paths'], str):
                        property_data['image_paths'] = json.loads(property_data['image_paths'].replace("'", '"'))
                except:
                    property_data['image_paths'] = [property_data['image_paths']] if property_data['image_paths'] else []
            else:
                property_data['image_paths'] = []

        except Exception as e:
            flash(f'Error loading property: {str(e)}', 'error')
            return redirect('/admin/landlord-dashboard')
        finally:
            cursor.close()
            conn.close()

    return render_template('landlord/edit_property.html',
                           property=property_data,
                           regions=regions,
                           neighborhoods=neighborhoods)

@admin_bp.route('/admin/landlord/delete-property/<int:property_id>', methods=['POST'])
@landlord_only
def landlord_delete_property(property_id):
    """Landlord-only: Delete property (only their own)"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Verify the property belongs to this landlord before deleting
        cursor.execute("SELECT * FROM houses WHERE id = %s AND created_by = %s",
                       (property_id, session['user_id']))
        property_data = cursor.fetchone()

        if not property_data:
            flash('Property not found or access denied.', 'error')
            return redirect('/admin/landlord-dashboard')

        # Delete house images folder if exists
        import shutil
        house_folder = f'static/uploads/house_{property_id}'
        if os.path.exists(house_folder):
            shutil.rmtree(house_folder)

        cursor.execute("DELETE FROM houses WHERE id = %s AND created_by = %s",
                       (property_id, session['user_id']))
        conn.commit()
        flash('Property deleted successfully!', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error deleting property: {str(e)}', 'error')
    finally:
        cursor.close()
        conn.close()

    return redirect('/admin/landlord-dashboard')

@admin_bp.route('/admin/manage-houses')
@admin_only
def manage_houses():
    """Admin-only: Manage all houses"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Get all houses
        cursor.execute("""
            SELECT h.* 
            FROM houses h
            ORDER BY h.created_at DESC
        """)
        houses = cursor.fetchall()

        # Parse image_paths for each house
        for house in houses:
            if house['image_paths']:
                try:
                    if isinstance(house['image_paths'], str):
                        house['image_paths'] = json.loads(house['image_paths'].replace("'", '"'))
                except:
                    house['image_paths'] = [house['image_paths']] if house['image_paths'] else []
            else:
                house['image_paths'] = []

    except Exception as e:
        flash(f'Error loading houses: {str(e)}', 'error')
        houses = []
    finally:
        cursor.close()
        conn.close()

    return render_template('admin/manage_houses.html', houses=houses)

@admin_bp.route('/admin/edit-house/<int:house_id>', methods=['GET', 'POST'])
@admin_only
def edit_house(house_id):
    """Admin-only: Edit any house"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Get regions and neighborhoods for dropdowns
    cursor.execute("SELECT * FROM regions")
    regions = cursor.fetchall()

    cursor.execute("SELECT * FROM neighborhoods")
    neighborhoods = cursor.fetchall()

    if request.method == 'POST':
        try:
            # Get form data
            title = request.form['title']
            description = request.form['description']
            region_id = request.form.get('region_id')
            neighborhood_id = request.form.get('neighborhood_id')
            exact_location = request.form['exact_location']
            property_type = request.form['property_type']
            completion_status = request.form['completion_status']
            months_left = request.form.get('months_left') or None
            price = request.form['price']
            is_featured = 'is_featured' in request.form
            delete_images = request.form.getlist('delete_images')

            # Get contact information
            contact_name = request.form.get('contact_name')
            contact_phone = request.form.get('contact_phone')
            contact_email = request.form.get('contact_email')

            # Get current image paths
            cursor.execute("SELECT image_paths FROM houses WHERE id = %s", (house_id,))
            current_data = cursor.fetchone()
            current_images = []

            if current_data and current_data['image_paths']:
                try:
                    if isinstance(current_data['image_paths'], str):
                        current_images = json.loads(current_data['image_paths'].replace("'", '"'))
                except:
                    current_images = [current_data['image_paths']] if current_data['image_paths'] else []

            # Remove deleted images
            updated_images = [img for img in current_images if img not in delete_images]

            # Handle new image uploads
            if 'images' in request.files:
                files = request.files.getlist('images')
                new_images = save_uploaded_files(files, house_id)
                updated_images.extend(new_images)

            # If no images left, use placeholder
            if not updated_images:
                updated_images = ['house_placeholder.jpg']

            # Update house in database
            cursor.execute("""
                UPDATE houses 
                SET title = %s, description = %s, region_id = %s, neighborhood_id = %s,
                    exact_location = %s, property_type = %s, completion_status = %s,
                    months_left = %s, price = %s, is_featured = %s, 
                    image_paths = %s, updated_at = CURRENT_TIMESTAMP,
                    contact_name = %s, contact_phone = %s, contact_email = %s
                WHERE id = %s
            """, (title, description, region_id, neighborhood_id, exact_location,
                  property_type, completion_status, months_left, price, is_featured,
                  json.dumps(updated_images), contact_name, contact_phone, contact_email, house_id))

            conn.commit()
            flash('House updated successfully!', 'success')
            return redirect('/admin/manage-houses')

        except Exception as e:
            conn.rollback()
            flash(f'Error updating house: {str(e)}', 'error')
        finally:
            cursor.close()
            conn.close()

    else:
        # GET request - load existing house data
        try:
            cursor.execute("SELECT * FROM houses WHERE id = %s", (house_id,))
            house = cursor.fetchone()

            if not house:
                flash('House not found!', 'error')
                return redirect('/admin/manage-houses')

            # Parse image_paths if it's a string
            if house['image_paths']:
                try:
                    if isinstance(house['image_paths'], str):
                        house['image_paths'] = json.loads(house['image_paths'].replace("'", '"'))
                except:
                    house['image_paths'] = [house['image_paths']] if house['image_paths'] else []
            else:
                house['image_paths'] = []

        except Exception as e:
            flash(f'Error loading house: {str(e)}', 'error')
            return redirect('/admin/manage-houses')
        finally:
            cursor.close()
            conn.close()

    return render_template('admin/edit_house.html',
                           house=house,
                           regions=regions,
                           neighborhoods=neighborhoods)

@admin_bp.route('/admin/delete-house/<int:house_id>', methods=['POST'])
@admin_only
def delete_house(house_id):
    """Admin-only: Delete any house"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Delete house images folder if exists
        import shutil
        house_folder = f'static/uploads/house_{house_id}'
        if os.path.exists(house_folder):
            shutil.rmtree(house_folder)

        cursor.execute("DELETE FROM houses WHERE id = %s", (house_id,))
        conn.commit()
        flash('House deleted successfully!', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error deleting house: {str(e)}', 'error')
    finally:
        cursor.close()
        conn.close()

    return redirect('/admin/manage-houses')

@admin_bp.route('/admin/manage-users')
@admin_only
def manage_users():
    """Admin-only: Manage users"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Get all users
        cursor.execute("SELECT * FROM users ORDER BY created_at DESC")
        users = cursor.fetchall()

        return render_template('admin/manage_users.html', users=users)

    except Exception as e:
        flash(f'Error loading users: {str(e)}', 'error')
        return redirect('/admin/dashboard')
    finally:
        cursor.close()
        conn.close()

@admin_bp.route('/admin/edit-user/<int:user_id>', methods=['GET', 'POST'])
@admin_only
def edit_user(user_id):
    """Admin-only: Edit users"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        try:
            # Get form data
            email = request.form['email']
            full_name = request.form['full_name']
            phone = request.form['phone']
            role = request.form['role']
            is_active = 'is_active' in request.form

            # Update user in database
            cursor.execute("""
                UPDATE users 
                SET email = %s, full_name = %s, phone = %s, role = %s, is_active = %s
                WHERE id = %s
            """, (email, full_name, phone, role, is_active, user_id))

            conn.commit()
            flash('User updated successfully!', 'success')
            return redirect('/admin/manage-users')

        except Exception as e:
            conn.rollback()
            flash(f'Error updating user: {str(e)}', 'error')
        finally:
            cursor.close()
            conn.close()

    else:
        # GET request - load user data
        try:
            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()

            if not user:
                flash('User not found!', 'error')
                return redirect('/admin/manage-users')

        except Exception as e:
            flash(f'Error loading user: {str(e)}', 'error')
            return redirect('/admin/manage-users')
        finally:
            cursor.close()
            conn.close()

    return render_template('admin/edit_user.html', user=user)

@admin_bp.route('/admin/delete-user/<int:user_id>', methods=['POST'])
@admin_only
def delete_user(user_id):
    """Admin-only: Delete users"""
    # Prevent admin from deleting themselves
    if user_id == session.get('user_id'):
        flash('You cannot delete your own account!', 'error')
        return redirect('/admin/manage-users')

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
        flash('User deleted successfully!', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error deleting user: {str(e)}', 'error')
    finally:
        cursor.close()
        conn.close()

    return redirect('/admin/manage-users')