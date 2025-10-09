from flask import Blueprint, render_template, request, redirect, flash, session, jsonify
from modules.database import get_db_connection
from datetime import datetime

report_bp = Blueprint('report', __name__)


@report_bp.route('/report-issue', methods=['GET', 'POST'])
def report_issue():
    """User report submission form"""
    if not session.get('logged_in'):
        flash('Please login to submit a report.', 'error')
        return redirect('/login')

    if request.method == 'POST':
        report_type = request.form['report_type']
        title = request.form['title']
        description = request.form['description']
        priority = request.form.get('priority', 'medium')

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO reports (user_id, report_type, title, description, priority, status)
                VALUES (%s, %s, %s, %s, %s, 'pending')
            """, (session['user_id'], report_type, title, description, priority))

            conn.commit()
            flash('Report submitted successfully! We will review it soon.', 'success')
            return redirect('/my-reports')

        except Exception as e:
            conn.rollback()
            flash(f'Error submitting report: {str(e)}', 'error')
        finally:
            cursor.close()
            conn.close()

    return render_template('user/report_issue.html')


@report_bp.route('/my-reports')
def my_reports():
    """User's report history"""
    if not session.get('logged_in'):
        flash('Please login to view your reports.', 'error')
        return redirect('/login')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT r.*, u.username 
            FROM reports r 
            JOIN users u ON r.user_id = u.id 
            WHERE r.user_id = %s 
            ORDER BY r.created_at DESC
        """, (session['user_id'],))
        reports = cursor.fetchall()

    except Exception as e:
        flash(f'Error loading reports: {str(e)}', 'error')
        reports = []
    finally:
        cursor.close()
        conn.close()

    return render_template('user/my_reports.html', reports=reports)

# Admin report routes will be added in the next phase
# Add these admin routes to your existing report_routes.py

@report_bp.route('/admin/reports')
def admin_reports():
    """Admin view all reports"""
    if not session.get('logged_in') or session.get('role') != 'admin':
        flash('Admin access required.', 'error')
        return redirect('/login')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Get all reports with user info
        cursor.execute("""
            SELECT r.*, u.username, u.email, u.full_name 
            FROM reports r 
            JOIN users u ON r.user_id = u.id 
            ORDER BY 
                CASE WHEN r.priority = 'urgent' THEN 1
                     WHEN r.priority = 'high' THEN 2
                     WHEN r.priority = 'medium' THEN 3
                     ELSE 4 END,
                r.created_at DESC
        """)
        reports = cursor.fetchall()

    except Exception as e:
        flash(f'Error loading reports: {str(e)}', 'error')
        reports = []
    finally:
        cursor.close()
        conn.close()

    return render_template('admin/manage_reports.html', reports=reports)


@report_bp.route('/admin/reports/<int:report_id>')
def admin_report_detail(report_id):
    """Admin view report details"""
    if not session.get('logged_in') or session.get('role') != 'admin':
        flash('Admin access required.', 'error')
        return redirect('/login')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Get report details with user info
        cursor.execute("""
            SELECT r.*, u.username, u.email, u.full_name 
            FROM reports r 
            JOIN users u ON r.user_id = u.id 
            WHERE r.id = %s
        """, (report_id,))
        report = cursor.fetchone()

        if not report:
            flash('Report not found.', 'error')
            return redirect('/admin/reports')

    except Exception as e:
        flash(f'Error loading report: {str(e)}', 'error')
        return redirect('/admin/reports')
    finally:
        cursor.close()
        conn.close()

    return render_template('admin/report_detail.html', report=report)


@report_bp.route('/admin/reports/<int:report_id>/update', methods=['POST'])
def admin_update_report(report_id):
    """Admin update report status"""
    if not session.get('logged_in') or session.get('role') != 'admin':
        flash('Admin access required.', 'error')
        return redirect('/login')

    status = request.form['status']
    notes = request.form.get('notes', '')

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE reports 
            SET status = %s, updated_at = CURRENT_TIMESTAMP 
            WHERE id = %s
        """, (status, report_id))

        conn.commit()
        flash('Report status updated successfully!', 'success')

    except Exception as e:
        conn.rollback()
        flash(f'Error updating report: {str(e)}', 'error')
    finally:
        cursor.close()
        conn.close()

    return redirect(f'/admin/reports/{report_id}')