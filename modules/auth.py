from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from modules.database import get_db_connection
from werkzeug.security import generate_password_hash, check_password_hash
import re

auth_bp = Blueprint('auth', __name__)

# Helper function to validate email
def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        full_name = request.form['full_name']
        phone = request.form['phone']
        role = request.form['role']

        # Validation
        if not all([username, email, password, confirm_password, full_name]):
            flash('All fields are required!', 'error')
            return render_template('auth/register.html')

        if not is_valid_email(email):
            flash('Please enter a valid email address!', 'error')
            return render_template('auth/register.html')

        if password != confirm_password:
            flash('Passwords do not match!', 'error')
            return render_template('auth/register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters long!', 'error')
            return render_template('auth/register.html')

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            # Check if username or email already exists
            cursor.execute("SELECT * FROM users WHERE username = %s OR email = %s", (username, email))
            existing_user = cursor.fetchone()

            if existing_user:
                if existing_user['username'] == username:
                    flash('Username already exists!', 'error')
                else:
                    flash('Email already registered!', 'error')
                return render_template('auth/register.html')

            # Hash password and create user
            hashed_password = generate_password_hash(password)

            cursor.execute("""
                INSERT INTO users (username, email, password_hash, full_name, phone, role)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (username, email, hashed_password, full_name, phone, role))

            conn.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect('/login')  # CHANGED: Direct path

        except Exception as e:
            conn.rollback()
            flash(f'Registration failed: {str(e)}', 'error')
        finally:
            cursor.close()
            conn.close()

    return render_template('auth/register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user_type = request.form.get('user_type', 'tenant')  # tenant, landlord, admin

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            # Find user by username or email
            cursor.execute("SELECT * FROM users WHERE username = %s OR email = %s", (username, username))
            user = cursor.fetchone()

            if user and check_password_hash(user['password_hash'], password):
                # Check if user role matches the selected user_type
                if user_type == 'admin' and user['role'] != 'admin':
                    flash('Admin access denied!', 'error')
                elif user_type == 'landlord' and user['role'] not in ['landlord', 'admin']:
                    flash('Landlord access denied!', 'error')
                else:
                    # UPDATE: Track login activity
                    cursor.execute("""
                        UPDATE users 
                        SET last_login = CURRENT_TIMESTAMP, 
                            login_count = login_count + 1 
                        WHERE id = %s
                    """, (user['id'],))

                    # UPDATE: Log user activity
                    cursor.execute("""
                        INSERT INTO user_activities (user_id, activity_type, description, ip_address)
                        VALUES (%s, 'login', 'User logged into the system', %s)
                    """, (user['id'], request.remote_addr))

                    conn.commit()

                    # Track user session and engagement
                    try:
                        from modules.analytics_tracking import track_user_session, update_user_engagement
                        import uuid
                        
                        session_id = str(uuid.uuid4())
                        session['session_id'] = session_id
                        
                        track_user_session(
                            user_id=user['id'],
                            session_id=session_id,
                            ip_address=request.remote_addr,
                            user_agent=request.headers.get('User-Agent')
                        )
                        
                        update_user_engagement(user['id'], 'login')
                    except Exception as e:
                        print(f"Error tracking user session: {e}")

                    # Successful login
                    session['user_id'] = user['id']
                    session['username'] = user['username']
                    session['role'] = user['role']
                    session['logged_in'] = True

                    flash(f'Welcome back, {user["full_name"]}!', 'success')

                    # Redirect based on role - UPDATED to direct paths
                    if user['role'] == 'admin':
                        return redirect('/admin/dashboard')  # CHANGED: Direct path
                    elif user['role'] == 'landlord':
                        return redirect('/admin/landlord-dashboard')  # CHANGED: Direct path
                    else:
                        return redirect('/user/tenant-dashboard')  # CHANGED: Direct path
            else:
                flash('Invalid username or password!', 'error')

        except Exception as e:
            flash(f'Login error: {str(e)}', 'error')
        finally:
            cursor.close()
            conn.close()

    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect('/')  # CHANGED: Direct path to home

# Profile page
@auth_bp.route('/profile')
def profile():
    if not session.get('logged_in'):
        flash('Please login to view your profile.', 'error')
        return redirect('/login')  # CHANGED: Direct path

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("SELECT * FROM users WHERE id = %s", (session['user_id'],))
        user = cursor.fetchone()
    except Exception as e:
        flash(f'Error loading profile: {str(e)}', 'error')
        return redirect('/')  # CHANGED: Direct path to home
    finally:
        cursor.close()
        conn.close()

    return render_template('auth/profile.html', user=user)

@auth_bp.route('/profile/edit', methods=['GET', 'POST'])
def edit_profile():
    if not session.get('logged_in'):
        flash('Please login to edit your profile.', 'error')
        return redirect('/login')  # CHANGED: Direct path

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        try:
            # Get form data
            email = request.form['email']
            full_name = request.form['full_name']
            phone = request.form['phone']
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')

            # Basic validation
            if not email or not full_name:
                flash('Email and Full Name are required!', 'error')
                return redirect('/profile/edit')  # CHANGED: Direct path

            if not is_valid_email(email):
                flash('Please enter a valid email address!', 'error')
                return redirect('/profile/edit')  # CHANGED: Direct path

            # Check if email is already taken by another user
            cursor.execute("SELECT id FROM users WHERE email = %s AND id != %s",
                           (email, session['user_id']))
            if cursor.fetchone():
                flash('Email already registered by another user!', 'error')
                return redirect('/profile/edit')  # CHANGED: Direct path

            # Update query base
            update_query = "UPDATE users SET email = %s, full_name = %s, phone = %s"
            params = [email, full_name, phone]

            # Handle password change if provided
            if current_password and new_password:
                # Verify current password
                cursor.execute("SELECT password_hash FROM users WHERE id = %s", (session['user_id'],))
                user = cursor.fetchone()

                if not check_password_hash(user['password_hash'], current_password):
                    flash('Current password is incorrect!', 'error')
                    return redirect('/profile/edit')  # CHANGED: Direct path

                if new_password != confirm_password:
                    flash('New passwords do not match!', 'error')
                    return redirect('/profile/edit')  # CHANGED: Direct path

                if len(new_password) < 6:
                    flash('New password must be at least 6 characters long!', 'error')
                    return redirect('/profile/edit')  # CHANGED: Direct path

                # Add password to update
                update_query += ", password_hash = %s"
                params.append(generate_password_hash(new_password))

            # Complete the update query
            update_query += " WHERE id = %s"
            params.append(session['user_id'])

            # Execute update
            cursor.execute(update_query, params)
            conn.commit()

            # Update session data
            session['username'] = email.split('@')[0]  # Update username from email

            flash('Profile updated successfully!', 'success')
            return redirect('/profile')  # CHANGED: Direct path

        except Exception as e:
            conn.rollback()
            flash(f'Error updating profile: {str(e)}', 'error')
        finally:
            cursor.close()
            conn.close()

    else:
        # GET request - load current user data
        try:
            cursor.execute("SELECT * FROM users WHERE id = %s", (session['user_id'],))
            user = cursor.fetchone()
        except Exception as e:
            flash(f'Error loading profile: {str(e)}', 'error')
            return redirect('/profile')  # CHANGED: Direct path
        finally:
            cursor.close()
            conn.close()

    return render_template('auth/edit_profile.html', user=user)