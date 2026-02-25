from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'donara-secret-key-2026-change-in-production'

# XAMPP MySQL Config
MYSQL_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  
    'database': 'food_database',
}

def get_db_connection():
    try:
        return mysql.connector.connect(**MYSQL_CONFIG)
    except mysql.connector.Error:
        return None

def init_db():
    conn = get_db_connection()
    if conn is None:
        return
    cursor = conn.cursor()
    # Ensure columns exist to match signup logic
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users_fd (
            user_email VARCHAR(120) PRIMARY KEY,
            password VARCHAR(255) NOT NULL,
            Name VARCHAR(255),
            Phoneno VARCHAR(20)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS donations (
            id INT AUTO_INCREMENT PRIMARY KEY,
            food_name VARCHAR(255) NOT NULL,
            donor_name VARCHAR(255) NOT NULL,
            donor_phone VARCHAR(30) NOT NULL,
            kg DECIMAL(10,2) NOT NULL,
            pickup_time DATETIME NOT NULL,
            location_link TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS claims (
            id INT AUTO_INCREMENT PRIMARY KEY,
            donation_id INT NOT NULL,
            food_name VARCHAR(255) NOT NULL,
            donor_name VARCHAR(255) NOT NULL,
            donor_phone VARCHAR(30) NOT NULL,
            kg DECIMAL(10,2) NOT NULL,
            pickup_time DATETIME NOT NULL,
            location_link TEXT NOT NULL,
            receiver_name VARCHAR(255) NOT NULL,
            receiver_phone VARCHAR(30) NOT NULL,
            receiver_email VARCHAR(255) NOT NULL,
            receiver_location TEXT NOT NULL,
            receiver_address TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()

init_db()

@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['user_email']
        password = request.form['password']
        
        conn = get_db_connection()
        if conn is None:
            flash('Database unavailable. Please try again later.', 'error')
            return render_template('LoginPage.html')
        cursor = conn.cursor(dictionary=True) 
        
        # CHANGED: Use 'password' instead of 'password_hash' to match your DB schema
        query = "SELECT user_email, password FROM users_fd WHERE user_email = %s"
        cursor.execute(query, (email,))
        user = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        # CHANGED: Check 'password' key from the dictionary
        if user and check_password_hash(user['password'], password):
            session['user_email'] = user['user_email']
            flash('Login successful! Welcome back...', 'success')
            
            # CHANGED: Redirect to 'fd' (the name of your function below)
            return redirect(url_for('fd')) 
        else:
            flash('Invalid email or password!', 'error')
    
    return render_template('LoginPage.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form['user_email']
        password = request.form['password']
        Name = request.form['Name']
        Phoneno = request.form['Phoneno']

        conn = get_db_connection()
        if conn is None:
            flash('Database unavailable. Please try again later.', 'error')
            return render_template('Signup.html')
        cursor = conn.cursor()
        cursor.execute("SELECT user_email FROM users_fd WHERE user_email = %s", (email,))
        
        if cursor.fetchone():
            flash('Email already registered! Please login.', 'error')
        else:
            hashed_password = generate_password_hash(password)
            cursor.execute(
                "INSERT INTO users_fd (user_email, password,Name,Phoneno) VALUES (%s, %s,%s,%s)",
                (email, hashed_password,Name,Phoneno)
            )
            conn.commit()
            flash('Account created successfully! Please login.', 'success')
            conn.close()
            return redirect(url_for('login')) # Redirect to login after signup
        
        cursor.close()
        conn.close()
    
    return render_template('Signup.html')

@app.route('/fd')
def fd():
    if 'user_email' not in session:
        flash('Please login to access dashboard', 'error')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    if conn is None:
        flash('Database unavailable. Please try again later.', 'error')
        return redirect(url_for('login'))
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM users_fd") 
    registered_users = cursor.fetchone()[0]
    
    cursor.close()
    conn.close()
    
    return render_template('main.html', 
                         user_email=session['user_email'],
                         registered_users=registered_users)

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('login'))


@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/index')
def index():
    return render_template('main.html')
@app.route('/receiver')
def receiver():
    return render_template('Receiver.html')


@app.route('/donate')
def donate():
    return render_template('donate.html')

DONATIONS = []

@app.route('/api/donations', methods=['GET', 'POST'])
def api_donations():
    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        food_name = data.get('food_name')
        donor_name = data.get('donor_name')
        donor_phone = data.get('donor_phone')
        kg = data.get('kg')
        pickup_time = data.get('pickup_time')
        location_link = data.get('location_link')
        if not all([food_name, donor_name, donor_phone, kg, pickup_time, location_link]):
            return jsonify({'error': 'missing_fields'}), 400
        conn = get_db_connection()
        if conn is None:
            new_id = len(DONATIONS) + 1
            DONATIONS.insert(0, {
                'id': new_id,
                'food_name': food_name,
                'donor_name': donor_name,
                'donor_phone': donor_phone,
                'kg': kg,
                'pickup_time': pickup_time,
                'location_link': location_link,
            })
            return jsonify({'ok': True, 'id': new_id}), 201
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO donations (food_name, donor_name, donor_phone, kg, pickup_time, location_link) VALUES (%s,%s,%s,%s,%s,%s)",
            (food_name, donor_name, donor_phone, kg, pickup_time, location_link)
        )
        conn.commit()
        new_id = cursor.lastrowid
        cursor.close()
        conn.close()
        return jsonify({'ok': True, 'id': new_id}), 201
    conn = get_db_connection()
    if conn is None:
        return jsonify(DONATIONS)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, food_name, donor_name, donor_phone, kg, pickup_time, location_link, created_at FROM donations ORDER BY id DESC")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(rows)

CLAIMS = []

@app.route('/api/claims', methods=['GET', 'POST'])
def api_claims():
    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        donation_id_raw = data.get('donation_id')
        try:
            donation_id = int(donation_id_raw) if str(donation_id_raw).strip().isdigit() else None
        except (TypeError, ValueError):
            donation_id = None
        food_name_input = data.get('food_name')
        receiver_name = data.get('receiver_name')
        receiver_phone = data.get('receiver_phone')
        receiver_email = data.get('receiver_email') or ''
        receiver_location = data.get('receiver_location')
        receiver_address = data.get('receiver_address')
        if not all([receiver_name, receiver_phone, receiver_location, receiver_address]):
            return jsonify({'error': 'missing_fields'}), 400
        conn = get_db_connection()
        if conn is None:
            idx = None
            if donation_id is not None:
                idx = next((i for i, d in enumerate(DONATIONS) if str(d.get('id')) == str(donation_id)), None)
            if idx is None and food_name_input:
                idx = next((i for i, d in enumerate(DONATIONS) if str(d.get('food_name')).lower() == str(food_name_input).lower()), None)
            if idx is None:
                return jsonify({'error': 'not_found'}), 404
            d = DONATIONS.pop(idx)
            new_id = len(CLAIMS) + 1
            CLAIMS.insert(0, {
                'id': new_id,
                'donation_id': d.get('id'),
                'food_name': d.get('food_name'),
                'donor_name': d.get('donor_name'),
                'donor_phone': d.get('donor_phone'),
                'kg': d.get('kg'),
                'pickup_time': d.get('pickup_time'),
                'location_link': d.get('location_link'),
                'receiver_name': receiver_name,
                'receiver_phone': receiver_phone,
                'receiver_email': receiver_email,
                'receiver_location': receiver_location,
                'receiver_address': receiver_address,
            })
            return jsonify({'ok': True, 'id': new_id}), 201
        cursor = conn.cursor(dictionary=True)
        row = None
        if donation_id is not None:
            cursor.execute("SELECT id, food_name, donor_name, donor_phone, kg, pickup_time, location_link FROM donations WHERE id=%s", (donation_id,))
            row = cursor.fetchone()
        if row is None and food_name_input:
            # exact match
            cursor.execute("SELECT id, food_name, donor_name, donor_phone, kg, pickup_time, location_link FROM donations WHERE food_name=%s ORDER BY id DESC LIMIT 1", (food_name_input.strip(),))
            row = cursor.fetchone()
        if row is None and food_name_input:
            # case-insensitive/partial fallback
            like_term = f"%{food_name_input.strip()}%"
            cursor.execute("SELECT id, food_name, donor_name, donor_phone, kg, pickup_time, location_link FROM donations WHERE LOWER(food_name) LIKE LOWER(%s) ORDER BY id DESC LIMIT 1", (like_term,))
        row = cursor.fetchone()
        if not row:
            cursor.close()
            conn.close()
            return jsonify({'error': 'not_found'}), 404
        cursor.execute("DELETE FROM donations WHERE id=%s", (row['id'],))
        cursor.execute(
            "INSERT INTO claims (donation_id, food_name, donor_name, donor_phone, kg, pickup_time, location_link, receiver_name, receiver_phone, receiver_email, receiver_location, receiver_address) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (row['id'], row['food_name'], row['donor_name'], row['donor_phone'], row['kg'], row['pickup_time'], row['location_link'], receiver_name, receiver_phone, receiver_email, receiver_location, receiver_address)
        )
        conn.commit()
        new_id = cursor.lastrowid
        cursor.close()
        conn.close()
        return jsonify({'ok': True, 'id': new_id}), 201
    conn = get_db_connection()
    if conn is None:
        return jsonify(CLAIMS)
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, donation_id, food_name, donor_name, donor_phone, kg, pickup_time, location_link, receiver_name, receiver_phone, receiver_email, receiver_location, receiver_address, created_at FROM claims ORDER BY id DESC")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(rows)

@app.route('/api/donations/<int:donation_id>', methods=['DELETE'])
def delete_donation(donation_id):
    conn = get_db_connection()
    if conn is None:
        idx = next((i for i, d in enumerate(DONATIONS) if int(d.get('id', 0)) == int(donation_id)), None)
        if idx is None:
            return jsonify({'error': 'not_found'}), 404
        DONATIONS.pop(idx)
        return jsonify({'ok': True}), 200
    cursor = conn.cursor()
    cursor.execute("DELETE FROM donations WHERE id=%s", (donation_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'ok': True}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
