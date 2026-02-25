from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector

app = Flask(__name__)

# MySQL connection (update with your credentials)
def get_db():
    return mysql.connector.connect(
        host='localhost',
        user='root',               # your MySQL username
        password=' ',    # your MySQL password
        database='food_database'
        
    )

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        # Table: users_fd with columns user_email and password
        cursor.execute("SELECT * FROM users_fd WHERE user_email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        # If using plaintext passwords (NOT recommended)
        if user and user['password'] == password:
            session['user_email'] = user['user_email']          # if you have an id column
            # If no id column, you can store email instead:
            # session['user_email'] = user['user_email']
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid email or password. Please sign up for an account.', 'danger')
            return redirect(url_for('login'))

    # GET request – show login form
    return render_template('LoginPage.html')

@app.route('/fd')
def home():
    # Optional: protect home page – check if user is logged in
    if 'user_id' not in session:
        flash('Please log in first.', 'warning')
        return redirect(url_for('login'))
    return render_template('main.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/receiver')
def profile():
    if 'user_email' not in session:
        flash('Please login to access dashboard', 'error')
        return redirect(url_for('login'))
    
    conn = get_db()
    if conn is None:
        flash('Database unavailable. Please try again later.', 'error')
        return redirect(url_for('login'))
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM users_fd") 
    registered_users = cursor.fetchone()[0]
    
    cursor.close()
    conn.close()
    
   

if __name__ == '__main__':
    app.run(debug=True)