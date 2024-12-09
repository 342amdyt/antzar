import sqlite3
import base64
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Function to create the admin login database and table if not present
def create_admin_login_db():
    conn = sqlite3.connect('admin_login.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin_login (
            UserName TEXT NOT NULL CHECK (LENGTH(UserName) BETWEEN 5 AND 25),
            Password TEXT NOT NULL CHECK (LENGTH(Password) BETWEEN 6 AND 25)
        )
    ''')
    cursor.execute('SELECT COUNT(*) FROM admin_login')
    if cursor.fetchone()[0] == 0:
        cursor.execute('INSERT INTO admin_login (UserName, Password) VALUES (?, ?)', ('Admin', 'Admin@123'))
    conn.commit()
    conn.close()

# Function to create the customer database and table if not present
def create_customer_db():
    conn = sqlite3.connect('customer.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customer (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL CHECK (LENGTH(name) BETWEEN 1 AND 100),
            passport_number TEXT NOT NULL UNIQUE,
            reference_number TEXT NOT NULL UNIQUE,
            contact_number TEXT NOT NULL CHECK (LENGTH(contact_number) BETWEEN 10 AND 15),
            job_designation TEXT NOT NULL,
            profile_picture BLOB
        )
    ''')
    conn.commit()
    conn.close()

# Function to convert binary data to base64 encoding
def image_to_base64(image_data):
    return base64.b64encode(image_data).decode('utf-8')

# Register the custom filter with Flask
app.jinja_env.filters['b64encode'] = image_to_base64

@app.route('/')
def index():
    return render_template('index.html')

#=========================================================
#=======================  Templats =======================
#=========================================================

@app.route('/eden_job_verification', methods=['GET', 'POST'])
def eden_job_verification():
    error = None
    customer_data = None

    if request.method == 'POST':
        passport_number = request.form.get('uname')
        reference_number = request.form.get('psw')

        # Connect to SQLite database
        conn = sqlite3.connect('customer.db')  # Use your actual database file path
        cursor = conn.cursor()

        # Query to fetch customer data
        cursor.execute(''' 
            SELECT * FROM customer 
            WHERE passport_number = ? 
            AND reference_number = ?
        ''', (passport_number, reference_number))

        # Fetch the first matching result
        customer_data = cursor.fetchone()

        if customer_data and customer_data[5]:  # Assuming customer_data[5] is the image field
            # Open the image file and encode it to base64
            try:
                with open(customer_data[5], "rb") as image_file:
                    # Read the image as bytes and encode it in base64
                    encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
                customer_data = list(customer_data)  # Convert tuple to list to modify it
                customer_data[5] = encoded_image  # Update with the base64-encoded image
            except Exception as e:
                error = f"An error occurred while processing the image: {str(e)}"

    return render_template('eden_job_verification.html', error=error, customer_data=customer_data)

if __name__ == '__main__':
    app.run(debug=True)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        conn = sqlite3.connect('admin_login.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM admin_login WHERE UserName = ? AND Password = ?', (username, password))
        user = cursor.fetchone()
        conn.close()

        if user:
            return redirect(url_for('dashboard'))
        else:
            error = "Invalid username or password."

    return render_template('admin.html', error=error)

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/add_customer', methods=['POST'])
def add_customer():
    name = request.form['name']
    passport_number = request.form['passport_number']
    reference_number = request.form['reference_number']
    contact_number = request.form['contact_number']
    job_designation = request.form['job_designation']
    profile_picture = request.files['profile_picture'].read()  # Read profile picture as binary data

    conn = sqlite3.connect('customer.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO customer (name, passport_number, reference_number, contact_number, job_designation, profile_picture)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (name, passport_number, reference_number, contact_number, job_designation, profile_picture))
    conn.commit()
    conn.close()

    return render_template('dashboard.html', message="Customer added successfully!")

if __name__ == '__main__':
    create_admin_login_db()
    create_customer_db()
    app.run(debug=True)
