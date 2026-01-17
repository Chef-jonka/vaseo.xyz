#!/usr/bin/env python3
"""
LLM Acceptably Report - Client Portal
A simple Flask app for clients to view their AI bot traffic analysis reports.
"""

import os
import sqlite3
import secrets
import re
from functools import wraps
from pathlib import Path
from datetime import datetime
from werkzeug.utils import secure_filename
from io import StringIO

from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, send_from_directory, abort, Response
)
import bcrypt

# Import the AI bot analyzer
from aibot import AIBotAnalyzer, get_config
from report_generators.html_generator import generate_html_report

# Check if PostgreSQL is available
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    import psycopg
    USE_POSTGRES = True
else:
    USE_POSTGRES = False

# Configuration
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))
app.config['DATABASE'] = os.path.join(os.path.dirname(__file__), 'database.db')
app.config['REPORTS_DIR'] = os.path.join(os.path.dirname(__file__), 'reports')
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
ALLOWED_EXTENSIONS = {'log', 'txt'}

def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Database helpers
def get_db():
    """Get database connection."""
    if USE_POSTGRES:
        # Fix Render's postgres:// URL to postgresql://
        db_url = DATABASE_URL
        if db_url.startswith('postgres://'):
            db_url = db_url.replace('postgres://', 'postgresql://', 1)
        conn = psycopg.connect(db_url)
        return conn
    else:
        conn = sqlite3.connect(app.config['DATABASE'])
        conn.row_factory = sqlite3.Row
        return conn

def init_db():
    """Initialize the database with tables and default users."""
    conn = get_db()
    cursor = conn.cursor()

    if USE_POSTGRES:
        # PostgreSQL syntax
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                client_id TEXT,
                is_admin INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                company_name TEXT
            )
        ''')

        # Create reports table for persistent storage
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reports (
                id SERIAL PRIMARY KEY,
                client_id TEXT NOT NULL,
                filename TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(client_id, filename)
            )
        ''')

        # Check if demo user exists
        cursor.execute('SELECT id FROM users WHERE username = %s', ('demo',))
        if not cursor.fetchone():
            demo_hash = bcrypt.hashpw('demo123'.encode('utf-8'), bcrypt.gensalt())
            cursor.execute(
                'INSERT INTO users (username, password_hash, client_id, is_admin) VALUES (%s, %s, %s, %s)',
                ('demo', demo_hash.decode('utf-8'), 'demo-client', 0)
            )
            print("Created demo user: demo / demo123")

        # Check if admin user exists
        cursor.execute('SELECT id FROM users WHERE username = %s', ('admin',))
        if not cursor.fetchone():
            admin_hash = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt())
            cursor.execute(
                'INSERT INTO users (username, password_hash, client_id, is_admin) VALUES (%s, %s, %s, %s)',
                ('admin', admin_hash.decode('utf-8'), None, 1)
            )
            print("Created admin user: admin / admin123")
    else:
        # SQLite syntax
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                client_id TEXT,
                is_admin INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        ''')

        # Create reports table for persistent storage
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id TEXT NOT NULL,
                filename TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(client_id, filename)
            )
        ''')

        # Add last_login column if it doesn't exist (for existing databases)
        try:
            cursor.execute('ALTER TABLE users ADD COLUMN last_login TIMESTAMP')
        except sqlite3.OperationalError:
            pass  # Column already exists

        # Add company_name column if it doesn't exist
        try:
            cursor.execute('ALTER TABLE users ADD COLUMN company_name TEXT')
        except sqlite3.OperationalError:
            pass  # Column already exists

        # Check if demo user exists
        cursor.execute('SELECT id FROM users WHERE username = ?', ('demo',))
        if not cursor.fetchone():
            demo_hash = bcrypt.hashpw('demo123'.encode('utf-8'), bcrypt.gensalt())
            cursor.execute(
                'INSERT INTO users (username, password_hash, client_id, is_admin) VALUES (?, ?, ?, ?)',
                ('demo', demo_hash.decode('utf-8'), 'demo-client', 0)
            )
            print("Created demo user: demo / demo123")

        # Check if admin user exists
        cursor.execute('SELECT id FROM users WHERE username = ?', ('admin',))
        if not cursor.fetchone():
            admin_hash = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt())
            cursor.execute(
                'INSERT INTO users (username, password_hash, client_id, is_admin) VALUES (?, ?, ?, ?)',
                ('admin', admin_hash.decode('utf-8'), None, 1)
            )
            print("Created admin user: admin / admin123")

    conn.commit()
    conn.close()

def get_user(username):
    """Get user by username."""
    conn = get_db()
    cursor = conn.cursor()
    if USE_POSTGRES:
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        user = cursor.fetchone()
        if user:
            # Convert to dict-like for consistency
            columns = [desc[0] for desc in cursor.description]
            user = dict(zip(columns, user))
    else:
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
    conn.close()
    return user

def get_all_clients():
    """Get all non-admin users with report counts."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, client_id, created_at, last_login, company_name FROM users WHERE is_admin = 0 ORDER BY created_at DESC')
    clients = cursor.fetchall()

    if USE_POSTGRES:
        columns = [desc[0] for desc in cursor.description]
        clients = [dict(zip(columns, row)) for row in clients]

    conn.close()

    # Add report count for each client
    clients_with_reports = []
    for client in clients:
        if USE_POSTGRES:
            client_dict = client
        else:
            client_dict = dict(client)
        reports = get_client_reports(client_dict.get('client_id') or client.get('client_id'))
        client_dict['report_count'] = len(reports)
        clients_with_reports.append(client_dict)

    return clients_with_reports

def create_user(username, password, client_id, is_admin=False, company_name=None):
    """Create a new user."""
    conn = get_db()
    cursor = conn.cursor()

    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    try:
        if USE_POSTGRES:
            cursor.execute(
                'INSERT INTO users (username, password_hash, client_id, is_admin, company_name) VALUES (%s, %s, %s, %s, %s)',
                (username, password_hash.decode('utf-8'), client_id, 1 if is_admin else 0, company_name)
            )
        else:
            cursor.execute(
                'INSERT INTO users (username, password_hash, client_id, is_admin, company_name) VALUES (?, ?, ?, ?, ?)',
                (username, password_hash.decode('utf-8'), client_id, 1 if is_admin else 0, company_name)
            )
        conn.commit()

        # Create client reports folder (for local development)
        if client_id and not USE_POSTGRES:
            client_dir = os.path.join(app.config['REPORTS_DIR'], client_id)
            os.makedirs(client_dir, exist_ok=True)

        conn.close()
        return True
    except Exception as e:
        conn.close()
        return False

def verify_password(stored_hash, password):
    """Verify a password against stored hash."""
    return bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))

def get_client_reports(client_id):
    """Get list of reports for a client with metadata."""
    if not client_id:
        return []

    if USE_POSTGRES:
        # Get reports from database
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT filename, content, created_at, modified_at FROM reports WHERE client_id = %s ORDER BY modified_at DESC',
            (client_id,)
        )
        rows = cursor.fetchall()
        conn.close()

        reports = []
        for row in rows:
            filename, content, created_at, modified_at = row
            modified_date = modified_at if modified_at else created_at

            # Extract summary from content
            summary = extract_report_summary_from_content(content)

            reports.append({
                'filename': filename,
                'name': filename.replace('.html', '').replace('-', ' ').title(),
                'size': len(content),
                'modified': modified_date.timestamp() if modified_date else 0,
                'modified_date': modified_date.strftime('%Y-%m-%d') if modified_date else '',
                'modified_formatted': modified_date.strftime('%b %d, %Y') if modified_date else '',
                'summary': summary
            })

        return reports
    else:
        # Get reports from filesystem
        client_dir = os.path.join(app.config['REPORTS_DIR'], client_id)

        if not os.path.exists(client_dir):
            os.makedirs(client_dir, exist_ok=True)
            return []

        reports = []
        for filename in os.listdir(client_dir):
            if filename.endswith('.html'):
                filepath = os.path.join(client_dir, filename)
                modified_time = os.path.getmtime(filepath)
                modified_date = datetime.fromtimestamp(modified_time)

                # Try to extract summary from report
                summary = extract_report_summary(filepath)

                reports.append({
                    'filename': filename,
                    'name': filename.replace('.html', '').replace('-', ' ').title(),
                    'size': os.path.getsize(filepath),
                    'modified': modified_time,
                    'modified_date': modified_date.strftime('%Y-%m-%d'),
                    'modified_formatted': modified_date.strftime('%b %d, %Y'),
                    'summary': summary
                })

        # Sort by modified time descending (newest first)
        reports.sort(key=lambda x: x['modified'], reverse=True)
        return reports

def extract_report_summary_from_content(content):
    """Extract key stats from report HTML content."""
    try:
        summary = {
            'total_requests': None,
            'success_rate': None,
            'health_status': None,
            'top_bot': None
        }

        # Extract total requests
        match = re.search(r'Total AI Requests</div>\s*<div[^>]*>([0-9,]+)</div>', content)
        if match:
            summary['total_requests'] = match.group(1)

        # Extract success rate from health status
        match = re.search(r'(\d+\.?\d*)% of AI bot requests successful', content)
        if match:
            summary['success_rate'] = match.group(1)

        # Extract health status
        if 'EXCELLENT' in content:
            summary['health_status'] = 'excellent'
        elif 'NEEDS ATTENTION' in content:
            summary['health_status'] = 'critical'
        elif 'GOOD' in content:
            summary['health_status'] = 'warning'

        # Extract most active bot
        match = re.search(r'Most Active Bot</div>\s*<div[^>]*>([^<]+)</div>', content)
        if match:
            summary['top_bot'] = match.group(1).strip()

        return summary
    except:
        return None

def extract_report_summary(filepath):
    """Extract key stats from a report HTML file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        return extract_report_summary_from_content(content)
    except:
        return None

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        if not session.get('is_admin'):
            flash('Admin access required.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def index():
    """Home page - redirect to dashboard or login."""
    if 'user_id' in session:
        if session.get('is_admin'):
            return redirect(url_for('admin'))
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page."""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            flash('Please enter both username and password.', 'error')
            return render_template('login.html')

        user = get_user(username)

        if user and verify_password(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['client_id'] = user['client_id']
            session['is_admin'] = bool(user['is_admin'])
            session['company_name'] = user.get('company_name')

            # Update last login time
            conn = get_db()
            cursor = conn.cursor()
            if USE_POSTGRES:
                cursor.execute('UPDATE users SET last_login = %s WHERE id = %s',
                             (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), user['id']))
            else:
                cursor.execute('UPDATE users SET last_login = ? WHERE id = ?',
                             (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), user['id']))
            conn.commit()
            conn.close()

            flash(f'Welcome back, {username}!', 'success')

            if user['is_admin']:
                return redirect(url_for('admin'))
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'error')

    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout and clear session."""
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Client dashboard showing their reports."""
    client_id = session.get('client_id')

    if session.get('is_admin'):
        return redirect(url_for('admin'))

    reports = get_client_reports(client_id)

    # Calculate stats
    stats = {
        'total_reports': len(reports),
        'last_report_date': reports[0]['modified_formatted'] if reports else None,
        'latest_health': reports[0]['summary']['health_status'] if reports and reports[0].get('summary') else None
    }

    return render_template('dashboard.html',
                         username=session.get('username'),
                         company_name=session.get('company_name'),
                         client_id=client_id,
                         reports=reports,
                         stats=stats)

@app.route('/upload', methods=['GET', 'POST'])
@admin_required
def upload():
    """Admin: Upload log file and generate report for a client."""
    # Get list of clients for dropdown
    clients = get_all_clients()

    if request.method == 'POST':
        # Get selected client
        client_id = request.form.get('client_id', '').strip()
        if not client_id:
            flash('Please select a client.', 'error')
            return render_template('upload.html', username=session.get('username'), clients=clients)

        # Check if file was uploaded
        if 'logfile' not in request.files:
            flash('No file selected.', 'error')
            return render_template('upload.html', username=session.get('username'), clients=clients)

        file = request.files['logfile']

        if file.filename == '':
            flash('No file selected.', 'error')
            return render_template('upload.html', username=session.get('username'), clients=clients)

        if not allowed_file(file.filename):
            flash('Invalid file type. Please upload a .log or .txt file.', 'error')
            return render_template('upload.html', username=session.get('username'), clients=clients)

        # Save uploaded file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], f'{client_id}_{timestamp}_{filename}')
        file.save(upload_path)

        try:
            # Run the AI bot analyzer
            config = get_config()
            analyzer = AIBotAnalyzer(config)

            report_data = analyzer.analyze_file(upload_path, ignore_homepage_redirects=True)

            if 'error' in report_data:
                flash(f'Analysis failed: {report_data["error"]}', 'error')
                os.remove(upload_path)  # Clean up uploaded file
                return redirect(url_for('upload'))

            # Generate HTML report
            report_name = request.form.get('report_name', '').strip()
            if not report_name:
                report_name = datetime.now().strftime('%B-%Y').lower()

            # Sanitize report name
            report_name = ''.join(c if c.isalnum() or c in '-_' else '-' for c in report_name.lower())
            report_filename = f'{report_name}.html'

            if USE_POSTGRES:
                # Generate report to a temporary file, then store in database
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as tmp:
                    tmp_path = tmp.name

                generate_html_report(report_data, tmp_path, ignore_homepage_redirects=True)

                # Read the generated HTML
                with open(tmp_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()

                os.remove(tmp_path)

                # Store in database
                conn = get_db()
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO reports (client_id, filename, content, modified_at)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (client_id, filename)
                    DO UPDATE SET content = EXCLUDED.content, modified_at = EXCLUDED.modified_at
                ''', (client_id, report_filename, html_content, datetime.now()))
                conn.commit()
                conn.close()
            else:
                # Store on filesystem
                client_reports_dir = os.path.join(app.config['REPORTS_DIR'], client_id)
                os.makedirs(client_reports_dir, exist_ok=True)

                report_path = os.path.join(client_reports_dir, report_filename)

                # Generate the HTML report
                generate_html_report(report_data, report_path, ignore_homepage_redirects=True)

            # Clean up uploaded file
            os.remove(upload_path)

            flash(f'Report "{report_name}" generated successfully for client: {client_id}', 'success')
            return redirect(url_for('admin'))

        except Exception as e:
            flash(f'Error processing file: {str(e)}', 'error')
            if os.path.exists(upload_path):
                os.remove(upload_path)
            return render_template('upload.html', username=session.get('username'), clients=clients)

    return render_template('upload.html', username=session.get('username'), clients=clients)

@app.route('/view/<client_id>/<report_filename>')
@login_required
def view_report(client_id, report_filename):
    """View a specific report."""
    # Security check: user can only view their own reports
    if not session.get('is_admin') and session.get('client_id') != client_id:
        abort(403)

    # Validate filename (prevent path traversal)
    if '..' in report_filename or '/' in report_filename:
        abort(400)

    if not report_filename.endswith('.html'):
        abort(400)

    if USE_POSTGRES:
        # Get report from database
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT content FROM reports WHERE client_id = %s AND filename = %s',
            (client_id, report_filename)
        )
        row = cursor.fetchone()
        conn.close()

        if not row:
            abort(404)

        return Response(row[0], mimetype='text/html')
    else:
        # Check file exists
        report_path = os.path.join(app.config['REPORTS_DIR'], client_id, report_filename)

        if not os.path.exists(report_path):
            abort(404)

        # Serve the HTML file
        return send_from_directory(
            os.path.join(app.config['REPORTS_DIR'], client_id),
            report_filename
        )

@app.route('/download/<client_id>/<report_filename>')
@login_required
def download_report(client_id, report_filename):
    """Download a specific report."""
    # Security check: user can only download their own reports
    if not session.get('is_admin') and session.get('client_id') != client_id:
        abort(403)

    # Validate filename
    if '..' in report_filename or '/' in report_filename:
        abort(400)

    if not report_filename.endswith('.html'):
        abort(400)

    if USE_POSTGRES:
        # Get report from database
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT content FROM reports WHERE client_id = %s AND filename = %s',
            (client_id, report_filename)
        )
        row = cursor.fetchone()
        conn.close()

        if not row:
            abort(404)

        response = Response(row[0], mimetype='text/html')
        response.headers['Content-Disposition'] = f'attachment; filename="{report_filename}"'
        return response
    else:
        report_path = os.path.join(app.config['REPORTS_DIR'], client_id, report_filename)

        if not os.path.exists(report_path):
            abort(404)

        return send_from_directory(
            os.path.join(app.config['REPORTS_DIR'], client_id),
            report_filename,
            as_attachment=True
        )

@app.route('/admin', methods=['GET', 'POST'])
@admin_required
def admin():
    """Admin panel to manage clients."""
    error = None
    success = None

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'add_client':
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')
            client_id = request.form.get('client_id', '').strip()
            company_name = request.form.get('company_name', '').strip() or None

            if not username or not password or not client_id:
                error = 'All fields are required.'
            elif len(password) < 6:
                error = 'Password must be at least 6 characters.'
            elif not client_id.replace('-', '').replace('_', '').isalnum():
                error = 'Client ID can only contain letters, numbers, hyphens, and underscores.'
            else:
                if create_user(username, password, client_id, company_name=company_name):
                    success = f'Client "{username}" created successfully!'
                else:
                    error = 'Username already exists.'

        elif action == 'delete_client':
            user_id = request.form.get('user_id')
            if user_id:
                conn = get_db()
                cursor = conn.cursor()
                if USE_POSTGRES:
                    cursor.execute('DELETE FROM users WHERE id = %s AND is_admin = 0', (user_id,))
                else:
                    cursor.execute('DELETE FROM users WHERE id = ? AND is_admin = 0', (user_id,))
                conn.commit()
                conn.close()
                success = 'Client deleted successfully.'

    clients = get_all_clients()

    return render_template('admin.html',
                         username=session.get('username'),
                         clients=clients,
                         error=error,
                         success=success)

@app.route('/admin/client/<client_id>')
@admin_required
def admin_client_reports(client_id):
    """Admin: View all reports for a specific client."""
    # Get client info
    conn = get_db()
    cursor = conn.cursor()
    if USE_POSTGRES:
        cursor.execute('SELECT username, client_id, created_at, last_login FROM users WHERE client_id = %s AND is_admin = 0', (client_id,))
        row = cursor.fetchone()
        if row:
            columns = [desc[0] for desc in cursor.description]
            client = dict(zip(columns, row))
        else:
            client = None
    else:
        cursor.execute('SELECT username, client_id, created_at, last_login FROM users WHERE client_id = ? AND is_admin = 0', (client_id,))
        client = cursor.fetchone()
        if client:
            client = dict(client)
    conn.close()

    if not client:
        flash('Client not found.', 'error')
        return redirect(url_for('admin'))

    reports = get_client_reports(client_id)

    return render_template('admin_client.html',
                         username=session.get('username'),
                         client=client,
                         reports=reports)

@app.route('/admin/report/rename', methods=['POST'])
@admin_required
def rename_report():
    """Admin: Rename a report."""
    client_id = request.form.get('client_id', '').strip()
    old_filename = request.form.get('old_filename', '').strip()
    new_name = request.form.get('new_name', '').strip()

    if not client_id or not old_filename or not new_name:
        flash('Missing required fields.', 'error')
        return redirect(url_for('admin'))

    # Validate filenames
    if '..' in old_filename or '/' in old_filename:
        flash('Invalid filename.', 'error')
        return redirect(url_for('admin_client_reports', client_id=client_id))

    # Sanitize new name
    new_name = ''.join(c if c.isalnum() or c in '-_' else '-' for c in new_name.lower())
    new_filename = f'{new_name}.html'

    if USE_POSTGRES:
        conn = get_db()
        cursor = conn.cursor()

        # Check if old report exists
        cursor.execute('SELECT id FROM reports WHERE client_id = %s AND filename = %s', (client_id, old_filename))
        if not cursor.fetchone():
            conn.close()
            flash('Report not found.', 'error')
            return redirect(url_for('admin_client_reports', client_id=client_id))

        # Check if new filename already exists
        if old_filename != new_filename:
            cursor.execute('SELECT id FROM reports WHERE client_id = %s AND filename = %s', (client_id, new_filename))
            if cursor.fetchone():
                conn.close()
                flash('A report with that name already exists.', 'error')
                return redirect(url_for('admin_client_reports', client_id=client_id))

        try:
            cursor.execute('UPDATE reports SET filename = %s, modified_at = %s WHERE client_id = %s AND filename = %s',
                         (new_filename, datetime.now(), client_id, old_filename))
            conn.commit()
            flash(f'Report renamed to "{new_name}" successfully.', 'success')
        except Exception as e:
            flash(f'Error renaming report: {str(e)}', 'error')
        finally:
            conn.close()
    else:
        old_path = os.path.join(app.config['REPORTS_DIR'], client_id, old_filename)
        new_path = os.path.join(app.config['REPORTS_DIR'], client_id, new_filename)

        if not os.path.exists(old_path):
            flash('Report not found.', 'error')
            return redirect(url_for('admin_client_reports', client_id=client_id))

        if os.path.exists(new_path) and old_path != new_path:
            flash('A report with that name already exists.', 'error')
            return redirect(url_for('admin_client_reports', client_id=client_id))

        try:
            os.rename(old_path, new_path)
            flash(f'Report renamed to "{new_name}" successfully.', 'success')
        except Exception as e:
            flash(f'Error renaming report: {str(e)}', 'error')

    return redirect(url_for('admin_client_reports', client_id=client_id))

@app.route('/admin/report/delete', methods=['POST'])
@admin_required
def delete_report():
    """Admin: Delete a report."""
    client_id = request.form.get('client_id', '').strip()
    filename = request.form.get('filename', '').strip()

    if not client_id or not filename:
        flash('Missing required fields.', 'error')
        return redirect(url_for('admin'))

    # Validate filename
    if '..' in filename or '/' in filename:
        flash('Invalid filename.', 'error')
        return redirect(url_for('admin_client_reports', client_id=client_id))

    if USE_POSTGRES:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute('SELECT id FROM reports WHERE client_id = %s AND filename = %s', (client_id, filename))
        if not cursor.fetchone():
            conn.close()
            flash('Report not found.', 'error')
            return redirect(url_for('admin_client_reports', client_id=client_id))

        try:
            cursor.execute('DELETE FROM reports WHERE client_id = %s AND filename = %s', (client_id, filename))
            conn.commit()
            flash('Report deleted successfully.', 'success')
        except Exception as e:
            flash(f'Error deleting report: {str(e)}', 'error')
        finally:
            conn.close()
    else:
        report_path = os.path.join(app.config['REPORTS_DIR'], client_id, filename)

        if not os.path.exists(report_path):
            flash('Report not found.', 'error')
            return redirect(url_for('admin_client_reports', client_id=client_id))

        try:
            os.remove(report_path)
            flash('Report deleted successfully.', 'success')
        except Exception as e:
            flash(f'Error deleting report: {str(e)}', 'error')

    return redirect(url_for('admin_client_reports', client_id=client_id))

# Error handlers
@app.errorhandler(403)
def forbidden(e):
    return render_template('login.html', error='Access denied. You do not have permission to view this resource.'), 403

@app.errorhandler(404)
def not_found(e):
    return render_template('login.html', error='The requested resource was not found.'), 404

# Initialize database on startup
with app.app_context():
    init_db()

if __name__ == '__main__':
    print("\n" + "="*50)
    print("LLM Acceptably Report - Client Portal")
    print("="*50)
    print("\nDefault credentials:")
    print("  Demo user:  demo / demo123")
    print("  Admin user: admin / admin123")
    print("\nServer starting at: http://localhost:5000")
    print("="*50 + "\n")

    app.run(debug=True, host='0.0.0.0', port=5000)
