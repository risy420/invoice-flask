from flask import Flask, render_template, request, jsonify, redirect, url_for, session, g
from werkzeug.security import generate_password_hash, check_password_hash
import os
import csv
import re
from functools import wraps
from collections import defaultdict
# changes done
import mysql.connector
import csv
import os
import mysql.connector
# db_config = {
#     'host': 'localhost',
#     'user': 'root',
#     'password': 'Rit420@$',
#     'database': 'challan'
# }
# db_config = {
#     host='db4free.net',
#     user='root',         # your db4free username
#     password='Rit420@$',  # your db4free password
#     database='challan'
# }
# db_config = {
#     'host': os.environ.get("DB_HOST"),
#     'user': os.environ.get("DB_USER"),
#     'password': os.environ.get("DB_PASSWORD"),
#     'database': os.environ.get("DB_NAME")
# }
db_config = {
    'host': os.environ.get('DB_HOST'),
    'user': os.environ.get('DB_USER'),
    'password': os.environ.get('DB_PASSWORD'),
    'database': os.environ.get('DB_NAME'),
    'port': int(os.environ.get('DB_PORT', 3306))
}
def get_db():
    if 'db' not in g:
        g.db = mysql.connector.connect(**db_config)
        g.cursor = g.db.cursor()
    return g.db, g.cursor
app = Flask(__name__)
@app.teardown_appcontext
def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()
# Define the folder to save uploaded logos
UPLOAD_FOLDER = os.path.join("static", "uploads", "logos")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Create if not exists


app = Flask(__name__)
app.secret_key = 'your_super_secret_key_here' # **CHANGE THIS IN PRODUCTION**

# Directory to store CSV files
CSV_FOLDER = 'challan_data'
if not os.path.exists(CSV_FOLDER):
    os.makedirs(CSV_FOLDER)
# //////////////////

# Inside your app.py, near CSV_FOLDER definition
UPLOAD_FOLDER = 'static/uploads/logos'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'} # Define allowed image types

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']





# //////////////////
# CSV file for user profiles
PROFILE_CSV_FILE = 'my_profile.csv'
# PROFILE_HEADERS = ['Company Name', 'GST Number', 'Address', 'Phone', 'Email', 'Password Hash']
# PROFILE_HEADERS = ['Company Name', 'GST Number', 'Address', 'Phone', 'Email', 'Password Hash', 'Description']
# PROFILE_HEADERS = ['Company Name', 'GST Number', 'Address', 'Phone', 'Email', 'Description', 'Password Hash']
PROFILE_HEADERS = ['Company Name', 'GST Number', 'Address', 'Phone', 'Email', 'Description', 'Password Hash' , 'Logo Path']



# Ensure profile CSV exists with headers
if not os.path.exists(PROFILE_CSV_FILE):
    with open(PROFILE_CSV_FILE, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(PROFILE_HEADERS)

# --- Authentication Decorator ---
# def login_required(f):
#     @wraps(f)
#     def decorated_function(*args, **kwargs):
#         if 'company_name' not in session:
#             return redirect(url_for('login'))
#         return f(*args, **kwargs)
#     return decorated_function
from functools import wraps
from flask import redirect, url_for

def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('login'))
        return view(**kwargs)
    return wrapped_view

# --- Before Request to load user details ---
@app.before_request
# def load_logged_in_user():
#     company_name = session.get('company_name')
#     if company_name is None:
#         g.user = None
#     else:
#         g.user = get_user_data(company_name) # Load user data into Flask's global 'g' object
#         print(f"DEBUG: g.user for {company_name}: {g.user}")# this is the changed one 
# from flask import g, session

# @app.before_request
# def load_logged_in_user():
#     user_id = session.get('user_id')

#     if user_id is None:
#         g.user = None
#     else:
#         # Query DB for the user
#         cursor = conn.cursor()
#         cursor.execute('SELECT * FROM companies WHERE id = %s', (user_id,))
#         # g.user = cursor.fetchone()
#         user_row = cursor.fetchone()
#         if user_row:
#             g.user = {
#                 'id': user_row[0],
#                 'company_name': user_row[1],
#                 'email': user_row[2],
#                 'password_hash': user_row[3],
#                 'logo_path': user_row[4],  # update this if more fields exist
#                 # add other fields as needed
#             }
# @app.before_request
# def load_logged_in_user():
#     user_id = session.get("user_id")
#     if user_id is None:
#         g.user = None
#     else:
#         cursor.execute("SELECT id, company_name FROM companies WHERE id = %s", (user_id,))
#         user = cursor.fetchone()
#         if user:
#             g.user = {"id": user[0], "Company Name": user[1]}
#         else:
#             g.user = None
@app.before_request
def load_logged_in_user():
    user_id = session.get("user_id")
    if user_id is None:
        g.user = None
    else:
        # Get DB connection and cursor here
        conn, cursor = get_db() # Ensure get_db() is called to get conn and cursor

        # Select all relevant columns
        cursor.execute("SELECT id, company_name, gst_number, address, phone, email, description, logo_path FROM companies WHERE id = %s", (user_id,))
        user_row = cursor.fetchone()

        if user_row:
            g.user = {
                "id": user_row[0],
                "Company Name": user_row[1],
                "GST Number": user_row[2],
                "Address": user_row[3],
                "Phone": user_row[4],
                "Email": user_row[5],
                "Description": user_row[6],
                "Logo Path": user_row[7].replace("\\", "/") if user_row[7] else "" # Handle logo path if present
            }
        else:
            g.user = None


def get_user_data(company_name):
    """Reads a single user's data from my_profile.csv."""
    if not os.path.exists(PROFILE_CSV_FILE):
        return None
    try:
        with open(PROFILE_CSV_FILE, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row['Company Name'] == company_name:
                    return row
    except Exception as e:
        app.logger.error(f"Error reading user data for {company_name}: {e}")
    return None

def get_all_users_data():
    """Reads all user data from my_profile.csv."""
    users = []
    if not os.path.exists(PROFILE_CSV_FILE):
        return users
    try:
        with open(PROFILE_CSV_FILE, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                users.append(row)
    except Exception as e:
        app.logger.error(f"Error reading all user data: {e}")
    return users


# --- Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_challan')
@login_required
def add_challan():
    return render_template('add_challan.html')

@app.route('/company_view')
@login_required
def company_view():
    return render_template('company_view.html')

# @app.route('/generate_invoice')
# @login_required
# def generate_invoice():
#     # Pass the logged-in user's profile data (sender's details) to the template
#     return render_template('generate_invoice.html', sender_details=g.user)
@app.route('/generate_invoice')
@login_required
def generate_invoice():
    # --- ADD THIS LINE FOR DEBUGGING ---
    print(f"DEBUG: g.user in generate_invoice: {g.user}")
    # --- END DEBUG LINE ---

    sender_details = g.user

    if not sender_details:
        print("DEBUG: Sender details are empty or None, redirecting to profile.")
        flash("Sender details not found. Please complete your profile.")
        return redirect(url_for('profile'))

    return render_template('generate_invoice.html', sender_details=sender_details)
# @app.route('/save_challan', methods=['POST'])
# @login_required
# def save_challan():
#     if not request.is_json:
#         return jsonify({"message": "Request must be JSON"}), 400

#     data = request.get_json()

#     company_name = data.get('companyName')
#     gst_number = data.get('gstNumber')
#     challan_date = data.get('challanDate')
#     challan_number = data.get('challanNumber')
#     products = data.get('products', [])

#     if not all([company_name, gst_number, challan_date, challan_number]):
#         return jsonify({"message": "Missing required challan details"}), 400

#     # Sanitize company name for filename
#     sanitized_company_name = re.sub(r'[^\w\s-]', '', company_name).strip().replace(' ', '_')
#     csv_filename = os.path.join(CSV_FOLDER, f"{sanitized_company_name}.csv")

#     # Define CSV header
#     fieldnames = [
#         'Company Name', 'GST Number', 'Challan Date', 'Challan Number',
#         'Product Description', 'HSN Code', 'Quantity', 'Unit', 'Process'
#     ]

#     file_exists = os.path.exists(csv_filename)

#     try:
#         with open(csv_filename, 'a' if file_exists else 'w', newline='', encoding='utf-8') as csvfile:
#             writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

#             if not file_exists:
#                 writer.writeheader() # Write header only if file is new

#             for product in products:
#                 row = {
#                     'Company Name': company_name,
#                     'GST Number': gst_number,
#                     'Challan Date': challan_date,
#                     'Challan Number': challan_number,
#                     'Product Description': product.get('description', ''),
#                     'HSN Code': product.get('hsn', ''),
#                     'Quantity': product.get('quantity', ''),
#                     'Unit': product.get('unit', ''),
#                     'Process': product.get('process', '')
#                 }
#                 writer.writerow(row)

#         return jsonify({"message": f"Challan saved successfully for {company_name} in {csv_filename}"}), 200

#     except Exception as e:
#         app.logger.error(f"Error saving challan data to CSV: {e}")
#         return jsonify({"message": f"Failed to save challan: {str(e)}"}), 500

# @app.route('/save_challan', methods=['POST'])
# @login_required
# def save_challan():
#     if not request.is_json:
#         return jsonify({"message": "Request must be JSON"}), 400

#     data = request.get_json()

#     company_name = data.get('companyName').strip() # Receiver company name
#     gst_number = data.get('gstNumber').strip()
#     challan_date = data.get('challanDate')
#     challan_number = data.get('challanNumber').strip()
#     products = data.get('products', [])

#     if not all([company_name, challan_date, challan_number, products]):
#         return jsonify({"message": "Missing required challan details or products"}), 400

#     conn, cursor = get_db()
#     try:
#         # 1. Insert/Get Receiver ID
#         # Check if receiver already exists
#         cursor.execute("SELECT id FROM receivers WHERE company_name = %s", (company_name,))
#         receiver_id = cursor.fetchone()

#         if receiver_id:
#             receiver_id = receiver_id[0]
#         else:
#             # If not, insert new receiver details
#             cursor.execute(
#                 "INSERT INTO receivers (company_name, gst_number) VALUES (%s, %s)",
#                 (company_name, gst_number) # Add address, phone, email if collected in add_challan.html
#             )
#             conn.commit() # Commit receiver insert to get its ID
#             receiver_id = cursor.lastrowid # Get the ID of the newly inserted receiver

#         # 2. Insert into challan_headers
#         # Check if challan_number already exists for this receiver to prevent duplicates
#         cursor.execute("SELECT id FROM challan_headers WHERE challan_number = %s AND receiver_id = %s",
#                        (challan_number, receiver_id))
#         challan_header_id = cursor.fetchone()

#         if challan_header_id:
#             # If challan number already exists, you might want to update it
#             # or return an error, depending on your business logic.
#             # For now, let's assume we update the existing one or prevent duplicate.
#             # Here, we'll return an error to prevent duplicate challan numbers.
#             return jsonify({"message": f"Challan number {challan_number} already exists for {company_name}."}), 409
#         else:
#             sql_header = """
#                 INSERT INTO challan_headers (receiver_id, challan_date, challan_number)
#                 VALUES (%s, %s, %s)
#             """
#             cursor.execute(sql_header, (receiver_id, challan_date, challan_number))
#             conn.commit() # Commit header insert to get its ID
#             challan_header_id = cursor.lastrowid # Get the ID of the newly inserted challan header

#         # 3. Insert into challan_line_items for each product
#         for product in products:
#             sql_line_item = """
#                 INSERT INTO challan_line_items (
#                     challan_header_id, product_description, hsn_code, quantity, unit, process
#                 ) VALUES (%s, %s, %s, %s, %s, %s)
#             """
#             values = (
#                 challan_header_id,
#                 product.get('description', ''),
#                 product.get('hsn', ''),
#                 int(product.get('quantity', 0)), # Ensure quantity is integer
#                 product.get('unit', ''),
#                 product.get('process', '')
#             )
#             cursor.execute(sql_line_item, values)
#         conn.commit() # Commit all line items

#         return jsonify({"message": f"Challan {challan_number} saved successfully for {company_name} in MySQL!"}), 200

#     except mysql.connector.Error as err:
#         conn.rollback() # Rollback all changes if any error occurs
#         app.logger.error(f"Error saving challan data to MySQL: {err}")
#         return jsonify({"message": f"Failed to save challan: {str(err)}"}), 500
#     except Exception as e:
#         conn.rollback()
#         app.logger.error(f"Unexpected error saving challan data: {e}")
#         return jsonify({"message": f"Failed to save challan: {str(e)}"}), 500
# @app.route('/save_challan', methods=['POST'])
# @login_required
# def save_challan():
#     if not request.is_json:
#         return jsonify({"message": "Request must be JSON"}), 400

#     data = request.get_json()

#     company_name = data.get('companyName').strip() # Receiver company name
#     gst_number = data.get('gstNumber').strip()
#     challan_date = data.get('challanDate')
#     challan_number = data.get('challanNumber').strip()
#     products = data.get('products', [])

#     if not all([company_name, challan_date, challan_number, products]):
#         return jsonify({"message": "Missing required challan details or products"}), 400

#     # Get the ID of the currently logged-in company (sender)
#     if not g.user or 'id' not in g.user:
#         return jsonify({"message": "Sender company not logged in."}), 403
#     sender_company_id = g.user['id']

#     conn, cursor = get_db()
#     try:
#         # 1. Insert/Get Receiver ID
#         # Check if receiver already exists for THIS SENDER
#         cursor.execute(
#             "SELECT id FROM receivers WHERE company_name = %s AND sender_company_id = %s",
#             (company_name, sender_company_id)
#         )
#         receiver_id_row = cursor.fetchone()

#         if receiver_id_row:
#             receiver_id = receiver_id_row[0]
#         else:
#             # If not, insert new receiver details and link to the current sender
#             cursor.execute(
#                 "INSERT INTO receivers (company_name, gst_number, sender_company_id) VALUES (%s, %s, %s)",
#                 (company_name, gst_number, sender_company_id) # <-- ADDED sender_company_id here
#             )
#             conn.commit() # Commit receiver insert to get its ID
#             receiver_id = cursor.lastrowid # Get the ID of the newly inserted receiver

#         # 2. Insert into challan_headers
#         # Check if challan_number already exists for this receiver to prevent duplicates
#         cursor.execute("SELECT id FROM challan_headers WHERE challan_number = %s AND receiver_id = %s",
#                        (challan_number, receiver_id))
#         challan_header_id_row = cursor.fetchone()

#         if challan_header_id_row:
#             # If challan number already exists for this receiver, return an error
#             return jsonify({"message": f"Challan number {challan_number} already exists for {company_name}."}), 409
#         else:
#             sql_header = """
#                 INSERT INTO challan_headers (receiver_id, challan_date, challan_number)
#                 VALUES (%s, %s, %s)
#             """
#             cursor.execute(sql_header, (receiver_id, challan_date, challan_number))
#             conn.commit() # Commit header insert to get its ID
#             challan_header_id = cursor.lastrowid # Get the ID of the newly inserted challan header

#         # 3. Insert into challan_line_items for each product
#         for product in products:
#             sql_line_item = """
#                 INSERT INTO challan_line_items (
#                     challan_header_id, product_description, hsn_code, quantity, unit, process
#                 ) VALUES (%s, %s, %s, %s, %s, %s)
#             """
#             values = (
#                 challan_header_id,
#                 product.get('description', ''),
#                 product.get('hsn', ''),
#                 int(product.get('quantity', 0)), # Ensure quantity is integer
#                 product.get('unit', ''),
#                 product.get('process', '')
#             )
#             cursor.execute(sql_line_item, values)
#         conn.commit() # Commit all line items

#         return jsonify({"message": f"Challan {challan_number} saved successfully for {company_name} in MySQL!"}), 200

#     except mysql.connector.Error as err:
#         conn.rollback() # Rollback all changes if any error occurs
#         app.logger.error(f"Error saving challan data to MySQL: {err}")
#         return jsonify({"message": f"Failed to save challan: {str(err)}"}), 500
#     except Exception as e:
#         conn.rollback()
#         app.logger.error(f"Unexpected error saving challan data: {e}")
#         return jsonify({"message": f"Failed to save challan: {str(e)}"}), 500
    
# @app.route('/save_challan', methods=['POST'])
# @login_required
# def save_challan():
#     if not request.is_json:
#         return jsonify({"message": "Request must be JSON"}), 400

#     data = request.get_json()

#     # Safely get and strip values, returning a 400 if required fields are missing
#     company_name = data.get('companyName')
#     if company_name:
#         company_name = company_name.strip()
#     else:
#         return jsonify({"message": "Receiver Company Name is required."}), 400

#     gst_number = data.get('gstNumber')
#     if gst_number: # GST number is optional, so only strip if not None/empty
#         gst_number = gst_number.strip()
#     else:
#         gst_number = None # Ensure it's None if empty

#     challan_date = data.get('challanDate')
    
#     challan_number = data.get('challanNumber')
#     if challan_number:
#         challan_number = challan_number.strip()
#     else:
#         return jsonify({"message": "Challan Number is required."}), 400

#     products = data.get('products', [])

#     if not challan_date or not products: # company_name and challan_number are already checked
#         return jsonify({"message": "Missing required challan date or products."}), 400

#     # Get the ID of the currently logged-in company (sender)
#     if not g.user or 'id' not in g.user:
#         return jsonify({"message": "Sender company not logged in."}), 403
#     sender_company_id = g.user['id']

#     conn, cursor = get_db()
#     try:
#         # 1. Insert/Get Receiver ID
#         # Check if receiver already exists for THIS SENDER
#         cursor.execute(
#             "SELECT id FROM receivers WHERE company_name = %s AND sender_company_id = %s",
#             (company_name, sender_company_id)
#         )
#         receiver_id_row = cursor.fetchone()

#         if receiver_id_row:
#             receiver_id = receiver_id_row[0]
#             app.logger.info(f"Existing receiver '{company_name}' found for sender {sender_company_id} with ID {receiver_id}")
#         else:
#             # If not, insert new receiver details and link to the current sender
#             cursor.execute(
#                 "INSERT INTO receivers (company_name, gst_number, sender_company_id) VALUES (%s, %s, %s)",
#                 (company_name, gst_number, sender_company_id)
#             )
#             conn.commit() # Commit receiver insert to get its ID
#             receiver_id = cursor.lastrowid # Get the ID of the newly inserted receiver
#             app.logger.info(f"New receiver '{company_name}' added for sender {sender_company_id} with ID {receiver_id}")

#         # 2. Insert into challan_headers
#         # Check if challan_number already exists for this sender to prevent duplicates
#         cursor.execute(
#             "SELECT id FROM challan_headers WHERE challan_number = %s AND sender_company_id = %s",
#             (challan_number, sender_company_id)
#         )
#         challan_header_id_row = cursor.fetchone()

#         if challan_header_id_row:
#             # If challan number already exists for this sender, return an error
#             return jsonify({"message": f"Challan number {challan_number} already exists for your company."}), 409
#         else:
#             sql_header = """
#                 INSERT INTO challan_headers (receiver_id, challan_date, challan_number, sender_company_id)
#                 VALUES (%s, %s, %s, %s)
#             """
#             cursor.execute(sql_header, (receiver_id, challan_date, challan_number, sender_company_id))
#             conn.commit() # Commit header insert to get its ID
#             challan_header_id = cursor.lastrowid # Get the ID of the newly inserted challan header
#             app.logger.info(f"New challan '{challan_number}' created with ID {challan_header_id}")

#         # 3. Insert into challan_line_items for each product
#         for product in products:
#             sql_line_item = """
#                 INSERT INTO challan_line_items (
#                     challan_header_id, product_description, hsn_code, quantity, unit, process
#                 ) VALUES (%s, %s, %s, %s, %s, %s)
#             """
#             # Use float for quantity to handle decimals, default to 0.0 if not provided or invalid
#             quantity_val = float(product.get('quantity', 0)) if product.get('quantity') is not None else 0.0

#             values = (
#                 challan_header_id,
#                 product.get('description', ''),
#                 product.get('hsn', ''),
#                 quantity_val,
#                 product.get('unit', ''),
#                 product.get('process', '')
#             )
#             cursor.execute(sql_line_item, values)
#         conn.commit() # Commit all line items

#         return jsonify({"message": f"Challan {challan_number} saved successfully for {company_name} in MySQL!"}), 200

#     except mysql.connector.Error as err:
#         conn.rollback() # Rollback all changes if any error occurs
#         app.logger.error(f"Error saving challan data to MySQL: {err}")
#         return jsonify({"message": f"Failed to save challan: {str(err)}"}), 500
#     except Exception as e:
#         conn.rollback()
#         app.logger.error(f"Unexpected error saving challan data: {e}")
#         return jsonify({"message": f"Failed to save challan: {str(e)}"}), 500
# from collections import defaultdict # Make sure this is imported at the top
@app.route('/save_challan', methods=['POST'])
@login_required
def save_challan():
    if not request.is_json:
        return jsonify({"message": "Request must be JSON"}), 400

    data = request.get_json()

    # Safely get and strip values, returning a 400 if required fields are missing
    company_name = data.get('companyName')
    if company_name:
        company_name = company_name.strip()
    else:
        return jsonify({"message": "Receiver Company Name is required."}), 400

    gst_number = data.get('gstNumber')
    if gst_number: # GST number is optional for saving, but strip if provided
        gst_number = gst_number.strip()
    else:
        gst_number = None # Ensure it's None if empty or not sent

    # Get new fields for receiver (address, phone, email)
    address = data.get('address')
    if address:
        address = address.strip()
    else:
        address = None
    
    phone = data.get('phone')
    if phone:
        phone = phone.strip()
    else:
        phone = None

    email = data.get('email')
    if email:
        email = email.strip()
    else:
        email = None
    
    challan_date = data.get('challanDate')
    
    challan_number = data.get('challanNumber')
    if challan_number:
        challan_number = challan_number.strip()
    else:
        return jsonify({"message": "Challan Number is required."}), 400

    products = data.get('products', [])

    if not challan_date or not products: # company_name and challan_number are already checked
        return jsonify({"message": "Missing required challan date or products."}), 400

    # Get the ID of the currently logged-in company (sender)
    if not g.user or 'id' not in g.user:
        return jsonify({"message": "Sender company not logged in."}), 403
    sender_company_id = g.user['id']

    conn, cursor = get_db()
    try:
        # 1. Insert/Get Receiver ID
        # Check if receiver already exists for THIS SENDER
        cursor.execute(
            "SELECT id, gst_number, address, phone, email FROM receivers WHERE company_name = %s AND sender_company_id = %s",
            (company_name, sender_company_id)
        )
        receiver_id_row = cursor.fetchone()

        if receiver_id_row:
            receiver_id = receiver_id_row[0]
            existing_gst, existing_address, existing_phone, existing_email = receiver_id_row[1], receiver_id_row[2], receiver_id_row[3], receiver_id_row[4]
            app.logger.info(f"Existing receiver '{company_name}' found for sender {sender_company_id} with ID {receiver_id}")

            # Update receiver details if they've changed and new data is provided
            update_fields = []
            update_values = []
            
            # Only update if the new value is not None/empty AND different from existing
            # Note: For optional fields like GST, phone, email, if the new value is an empty string, 
            # we should update it to NULL in DB to clear it.
            if (gst_number is not None and gst_number != existing_gst) or \
               (gst_number is None and existing_gst is not None): # If new is None, and old exists, set old to None
                update_fields.append("gst_number = %s")
                update_values.append(gst_number)
            
            if (address is not None and address != existing_address) or \
               (address is None and existing_address is not None):
                update_fields.append("address = %s")
                update_values.append(address)

            if (phone is not None and phone != existing_phone) or \
               (phone is None and existing_phone is not None):
                update_fields.append("phone = %s")
                update_values.append(phone)

            if (email is not None and email != existing_email) or \
               (email is None and existing_email is not None):
                update_fields.append("email = %s")
                update_values.append(email)

            if update_fields:
                update_query = f"UPDATE receivers SET {', '.join(update_fields)} WHERE id = %s"
                update_values.append(receiver_id)
                cursor.execute(update_query, tuple(update_values))
                conn.commit()
                app.logger.info(f"Updated details for existing receiver '{company_name}' (ID: {receiver_id}).")

        else:
            # If not, insert new receiver details and link to the current sender
            cursor.execute(
                "INSERT INTO receivers (company_name, gst_number, address, phone, email, sender_company_id) VALUES (%s, %s, %s, %s, %s, %s)",
                (company_name, gst_number, address, phone, email, sender_company_id)
            )
            conn.commit() # Commit receiver insert to get its ID
            receiver_id = cursor.lastrowid # Get the ID of the newly inserted receiver
            app.logger.info(f"New receiver '{company_name}' added for sender {sender_company_id} with ID {receiver_id}")

        # 2. Insert into challan_headers
        # Check if challan_number already exists for this sender to prevent duplicates
        cursor.execute(
            "SELECT id FROM challan_headers WHERE challan_number = %s AND sender_company_id = %s",
            (challan_number, sender_company_id)
        )
        challan_header_id_row = cursor.fetchone()

        if challan_header_id_row:
            # If challan number already exists for this sender, return an error
            return jsonify({"message": f"Challan number {challan_number} already exists for your company."}), 409
        else:
            sql_header = """
                INSERT INTO challan_headers (receiver_id, challan_date, challan_number, sender_company_id)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(sql_header, (receiver_id, challan_date, challan_number, sender_company_id))
            conn.commit() # Commit header insert to get its ID
            challan_header_id = cursor.lastrowid # Get the ID of the newly inserted challan header
            app.logger.info(f"New challan '{challan_number}' created with ID {challan_header_id}")

        # 3. Insert into challan_line_items for each product
        for product in products:
            sql_line_item = """
                INSERT INTO challan_line_items (
                    challan_header_id, product_description, hsn_code, quantity, unit, process
                ) VALUES (%s, %s, %s, %s, %s, %s)
            """
            # Use float for quantity to handle decimals, default to 0.0 if not provided or invalid
            quantity_val = float(product.get('quantity', 0)) if product.get('quantity') is not None else 0.0

            values = (
                challan_header_id,
                product.get('description', ''),
                product.get('hsn', ''),
                quantity_val,
                product.get('unit', ''),
                product.get('process', '')
            )
            cursor.execute(sql_line_item, values)
        conn.commit() # Commit all line items

        return jsonify({"message": f"Challan {challan_number} saved successfully for {company_name} in MySQL!"}), 200

    except mysql.connector.Error as err:
        conn.rollback() # Rollback all changes if any error occurs
        app.logger.error(f"Error saving challan data to MySQL: {err}")
        return jsonify({"message": f"Failed to save challan: {str(err)}"}), 500
    except Exception as e:
        conn.rollback()
        app.logger.error(f"Unexpected error saving challan data: {e}")
        return jsonify({"message": f"Failed to save challan: {str(e)}"}), 500
# ... (your existing code) ...

@app.route('/get_receivers')
@login_required
def get_receivers():
    """
    Returns a list of receivers associated with the currently logged-in company.
    """
    conn, cursor = get_db()
    sender_company_id = g.user['id'] # Get the ID of the logged-in company
    print(f"DEBUG: Logged-in sender_company_id: {sender_company_id}") # ADD THIS LINE
    print(f"DEBUG: Attempting to fetch receivers for sender_company_id: {sender_company_id}") # ADD THIS LINE

    try:
        cursor.execute(
            "SELECT id, company_name, gst_number FROM receivers WHERE sender_company_id = %s ORDER BY company_name",
            (sender_company_id,)
        )
        receivers = cursor.fetchall()
        receiver_list = []
        for r_id, r_name, r_gst in receivers:
            receiver_list.append({"id": r_id, "company_name": r_name, "gst_number": r_gst})
        return jsonify({"receivers": receiver_list})
    except Exception as e:
        app.logger.error(f"Error fetching receivers for sender {sender_company_id}: {e}")
        return jsonify({"message": "Could not retrieve receivers", "error": str(e)}), 500

# @app.route('/company_list')
# @login_required
# def company_list():
#     """Returns a list of company names based on existing CSV files."""
#     companies = []
#     try:
#         for filename in os.listdir(CSV_FOLDER):
#             if filename.endswith('.csv'):
#                 company_name = os.path.splitext(filename)[0].replace('_', ' ')
#                 companies.append(company_name)
#     except Exception as e:
#         app.logger.error(f"Error listing companies: {e}")
#         return jsonify({"message": "Could not retrieve company list", "error": str(e)}), 500
#     return jsonify({"companies": sorted(companies)})
# Update company_list to fetch from receivers table
# @app.route('/company_list')
# @login_required
# def company_list():
#     """Returns a list of unique company names from the receivers table."""
#     conn, cursor = get_db()
#     companies = []
#     try:
#         cursor.execute("SELECT company_name FROM receivers ORDER BY company_name")
#         for row in cursor.fetchall():
#             companies.append(row[0])
#     except Exception as e:
#         app.logger.error(f"Error listing companies from DB: {e}")
#         return jsonify({"message": "Could not retrieve company list", "error": str(e)}), 500
#     return jsonify({"companies": sorted(companies)})
@app.route('/company_list')
@login_required
def company_list():
    """Returns a list of unique company names from the receivers table,
    filtered by the logged-in sender's company ID."""
    if not g.user or 'id' not in g.user:
        return jsonify({"message": "Not logged in or user ID not available."}), 401

    sender_company_id = g.user['id'] # Get the ID of the logged-in sender

    conn, cursor = get_db()
    companies = []
    try:
        # Fetch only company names (receivers) associated with the logged-in sender_company_id
        # Use DISTINCT to ensure only unique company names are returned if there are duplicates
        cursor.execute("SELECT DISTINCT company_name FROM receivers WHERE sender_company_id = %s ORDER BY company_name", (sender_company_id,))
        for row in cursor.fetchall():
            companies.append(row[0])
        return jsonify({"companies": companies}), 200 # Already sorted by the query
    except Exception as e:
        app.logger.error(f"Error listing companies from DB: {e}")
        return jsonify({"message": "Could not retrieve company list", "error": str(e)}), 500

# @app.route('/company_details/<company_name>')
# @login_required
# def company_details(company_name):
#     """Returns all challan details for a specific company."""
#     sanitized_company_name = re.sub(r'[^\w\s-]', '', company_name).strip().replace(' ', '_')
#     csv_filename = os.path.join(CSV_FOLDER, f"{sanitized_company_name}.csv")

#     if not os.path.exists(csv_filename):
#         return jsonify({"message": "Company not found"}), 404

#     details = []
#     try:
#         with open(csv_filename, 'r', newline='', encoding='utf-8') as csvfile:
#             reader = csv.DictReader(csvfile)
#             for row in reader:
#                 details.append(row)
#     except Exception as e:
#         app.logger.error(f"Error reading company details for {company_name}: {e}")
#         return jsonify({"message": "Could not retrieve company details", "error": str(e)}), 500
#     return jsonify({"company_name": company_name, "details": details})
# Update company_details to fetch from challan_headers and challan_line_items
# @app.route('/company_details/<company_name>')
# @login_required
# def company_details(company_name):
#     """
#     Returns all challan details (headers and line items) for a specific company.
#     """
#     conn, cursor = get_db()
#     challans_data = defaultdict(lambda: {'header': {}, 'products': []})

#     try:
#         # First, get the receiver_id
#         cursor.execute("SELECT id FROM receivers WHERE company_name = %s", (company_name,))
#         receiver_row = cursor.fetchone()
#         if not receiver_row:
#             return jsonify({"message": f"Company '{company_name}' not found."}), 404
#         receiver_id = receiver_row[0]

#         # Get all challan headers for this receiver
#         cursor.execute(
#             "SELECT id, challan_number, challan_date FROM challan_headers WHERE receiver_id = %s ORDER BY challan_date DESC, challan_number DESC",
#             (receiver_id,)
#         )
#         challan_headers = cursor.fetchall()

#         # For each challan header, get its line items
#         for header_id, challan_num, challan_date in challan_headers:
#             challans_data[challan_num]['header'] = {
#                 'id': header_id,
#                 'challan_number': challan_num,
#                 'challan_date': challan_date.strftime('%Y-%m-%d') if challan_date else None,
#                 'company_name': company_name # Redundant but useful for UI
#             }

#             cursor.execute(
#                 """
#                 SELECT product_description, hsn_code, quantity, unit, process
#                 FROM challan_line_items
#                 WHERE challan_header_id = %s
#                 ORDER BY id
#                 """,
#                 (header_id,)
#             )
#             line_items = cursor.fetchall()
#             # Convert line items to dictionaries for better readability
#             line_item_columns = [desc[0] for desc in cursor.description]
#             for item_row in line_items:
#                 challans_data[challan_num]['products'].append(dict(zip(line_item_columns, item_row)))

#     except Exception as e:
#         app.logger.error(f"Error reading company details for {company_name} from DB: {e}")
#         return jsonify({"message": "Could not retrieve company details", "error": str(e)}), 500

#     # Convert defaultdict to a regular dictionary of lists for JSON output
#     # Each item in the list will represent a unique challan
#     output_list = []
#     for challan_num in sorted(challans_data.keys(), reverse=True): # Sort by challan number for consistent order
#         output_list.append(challans_data[challan_num])

#     return jsonify({"company_name": company_name, "challans": output_list})

@app.route('/company_details/<company_name>')
@login_required
def company_details(company_name):
    conn, cursor = get_db()
    challans_data = defaultdict(lambda: {'header': {}, 'products': []})
    receiver_gst_number = None # Initialize to None

    try:
        # First, get the receiver's ID AND GST Number
        cursor.execute("SELECT id, gst_number FROM receivers WHERE company_name = %s", (company_name,))
        receiver_row = cursor.fetchone()

        if not receiver_row:
            return jsonify({"message": f"Company '{company_name}' not found."}), 404

        receiver_id = receiver_row[0]
        receiver_gst_number = receiver_row[1] # Store the GST number

        # Get all challan headers for this receiver
        cursor.execute(
            "SELECT id, challan_number, challan_date FROM challan_headers WHERE receiver_id = %s ORDER BY challan_date DESC, challan_number DESC",
            (receiver_id,)
        )
        challan_headers = cursor.fetchall()

        # For each challan header, get its line items (existing logic)
        for header_id, challan_num, challan_date in challan_headers:
            challans_data[challan_num]['header'] = {
                'id': header_id,
                'challan_number': challan_num,
                'challan_date': challan_date.strftime('%Y-%m-%d') if challan_date else None,
                'company_name': company_name
            }

            cursor.execute(
                """
                SELECT product_description, hsn_code, quantity, unit, process
                FROM challan_line_items
                WHERE challan_header_id = %s
                ORDER BY id
                """,
                (header_id,)
            )
            line_items = cursor.fetchall()
            line_item_columns = [desc[0] for desc in cursor.description]
            for item_row in line_items:
                challans_data[challan_num]['products'].append(dict(zip(line_item_columns, item_row)))

    except Exception as e:
        app.logger.error(f"Error reading company details for {company_name} from DB: {e}")
        return jsonify({"message": "Could not retrieve company details", "error": str(e)}), 500

    output_list = []
    for challan_num in sorted(challans_data.keys(), reverse=True):
        output_list.append(challans_data[challan_num])

    # Modify the return statement to include the GST number
    return jsonify({
        "company_name": company_name,
        "gst_number": receiver_gst_number, # ADDED: The receiver's GST number
        "challans": output_list,
        "details": [{"GST Number": receiver_gst_number}] # Added this to match JS expectation
    })

import os
import csv
import re
from collections import defaultdict # This import is already present in your app.py
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, g
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash # Ensure these are imported as they are in your app.py

# ... (your existing Flask app setup and other routes) ...

# @app.route('/get_company_products/<company_name>')
# @login_required
# def get_company_products(company_name):
#     """
#     Returns product details (description, HSN, quantity, unit, process, and original Challan Number)
#     for a specific company, suitable for pre-filling the delivery challan.
#     Each distinct line item from the source CSV will be returned as a separate product.
#     """
#     sanitized_company_name = re.sub(r'[^\w\s-]', '', company_name).strip().replace(' ', '_')
#     csv_filename = os.path.join(CSV_FOLDER, f"{sanitized_company_name}.csv")

#     if not os.path.exists(csv_filename):
#         return jsonify({"message": "Company not found"}), 404

#     products_list = []

#     try:
#         with open(csv_filename, 'r', newline='', encoding='utf-8') as csvfile:
#             reader = csv.DictReader(csvfile)
#             # Use a set to store unique product lines to avoid duplicates if the CSV has them
#             # based on (description, HSN, Quantity, Unit, Process, Challan Number)
#             seen_products = set()

#             for row in reader:
#                 desc = row.get('Product Description', '').strip()
#                 hsn = row.get('HSN Code', '').strip()
#                 qty = row.get('Quantity', '').strip()
#                 unit = row.get('Unit', '').strip()
#                 process = row.get('Process', '').strip()
#                 # Capture the Challan Number from this specific row
#                 challan_number_per_item = row.get('Challan Number', '').strip() 

#                 # Create a tuple to represent a unique product line for deduplication
#                 product_key = (desc, hsn, qty, unit, process, challan_number_per_item)

#                 if product_key not in seen_products:
#                     seen_products.add(product_key)
#                     products_list.append({
#                         'description': desc,
#                         'hsn': hsn,
#                         'quantity': qty,
#                         'unit': unit, # This will be mapped to 'weight' in JS
#                         'process': process,
#                         'challan_number_per_item': challan_number_per_item # Include the specific challan number for this product line
#                     })

#     except Exception as e:
#         app.logger.error(f"Error retrieving products for {company_name}: {e}")
#         return jsonify({"message": "Could not retrieve product details", "error": str(e)}), 500

#     return jsonify({"company_name": company_name, "products": products_list})
# Update get_company_products to fetch from challan_line_items
@app.route('/get_company_products/<company_name>')
@login_required
def get_company_products(company_name):
    """
    Returns product details (description, HSN, quantity, unit, process, and original Challan Number)
    for a specific company from the challans table, suitable for pre-filling the delivery challan.
    Each distinct line item from the source challans will be returned as a separate product.
    """
    conn, cursor = get_db()
    products_list = []

    try:
        # First, get the receiver_id
        cursor.execute("SELECT id FROM receivers WHERE company_name = %s", (company_name,))
        receiver_row = cursor.fetchone()
        if not receiver_row:
            return jsonify({"message": f"Company '{company_name}' not found."}), 404
        receiver_id = receiver_row[0]

        # Fetch distinct product lines for the given company by joining challan_headers and challan_line_items
        cursor.execute("""
            SELECT DISTINCT
                cli.product_description, cli.hsn_code, cli.quantity, cli.unit, cli.process, ch.challan_number
            FROM challan_line_items cli
            JOIN challan_headers ch ON cli.challan_header_id = ch.id
            WHERE ch.receiver_id = %s
            ORDER BY cli.product_description, cli.hsn_code
        """, (receiver_id,))

        for row in cursor.fetchall():
            products_list.append({
                'description': row[0] if row[0] is not None else '',
                'hsn': row[1] if row[1] is not None else '',
                'quantity': row[2] if row[2] is not None else 0,
                'unit': row[3] if row[3] is not None else '',
                'process': row[4] if row[4] is not None else '',
                'challan_number_per_item': row[5] if row[5] is not None else '' # Include the specific challan number for this product line
            })

    except Exception as e:
        app.logger.error(f"Error retrieving products for {company_name} from DB: {e}")
        return jsonify({"message": "Could not retrieve product details", "error": str(e)}), 500

    return jsonify({"company_name": company_name, "products": products_list})


import os
import csv
from werkzeug.security import generate_password_hash
from flask import render_template, request, redirect, url_for, flash

PROFILE_CSV_FILE = 'myprofile.csv'
PROFILE_HEADERS = ['Company Name', 'GST Number', 'Address', 'Phone', 'Email', 'Description', 'Password Hash', 'Logo Path']

# @app.route('/register', methods=['GET', 'POST'])
# def register():
#     if request.method == 'POST':
#         company_name = request.form['company_name']
#         gst_number = request.form['gst_number']
#         address = request.form['address']
#         phone = request.form['phone']
#         email = request.form['email']
#         description = request.form['description']
#         password = request.form['password']

#         new_user = {
#             'Company Name': company_name,
#             'GST Number': gst_number,
#             'Address': address,
#             'Phone': phone,
#             'Email': email,
#             'Description': description,
#             'Password Hash': generate_password_hash(password)
#         }

#         file_exists = os.path.isfile(PROFILE_CSV_FILE)

#         with open(PROFILE_CSV_FILE, 'a', newline='', encoding='utf-8') as csvfile:
#             writer = csv.DictWriter(csvfile, fieldnames=PROFILE_HEADERS)

#             # Write header only if file is new
#             if not file_exists:
#                 writer.writeheader()

#             writer.writerow(new_user)

#         flash('Account created successfully!', 'success')
#         return redirect(url_for('login'))

#     return render_template('register.html')
import csv
import os
import mysql.connector
from werkzeug.security import generate_password_hash
from flask import request, redirect, render_template

# MySQL connection setup (place this in a config file ideally)
# conn = mysql.connector.connect(
#     host="localhost",
#     user="root",
#     password="Rit420@$",
#     database="challan"
# )
conn = mysql.connector.connect(
    host="sql12.freesqldatabase.com",
    user="sql12793850",
    password="XtmBdMHs8T",
    database="sql12793850",
    port=3306
)
cursor = conn.cursor()

from werkzeug.security import generate_password_hash

from flask import Flask, render_template, request, redirect, flash
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
import os
import csv
import mysql.connector  # Or from flask_mysqldb import MySQL

UPLOAD_FOLDER = os.path.join("static", "uploads", "logos")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        company_name = request.form["company_name"]
        gst_number = request.form["gst_number"]
        address = request.form["address"]
        phone = request.form["phone"]
        email = request.form["email"]
        description = request.form["description"]
        password = request.form["password"]
        logo_path = ""

        # Handle optional logo
        # if 'logo' in request.files:
        #     logo = request.files['logo']
        #     if logo and logo.filename.strip() != "":
        #         filename = secure_filename(logo.filename)
        #         # logo_path = os.path.join("static", "uploads", "logos", filename)
        #         logo_path = os.path.join("uploads", "logos", filename)
        #         logo.save(logo_path)
        if 'logo' in request.files:
            logo = request.files['logo']
            if logo and logo.filename.strip() != "":
                filename = secure_filename(logo.filename)
                save_path = os.path.join(UPLOAD_FOLDER, filename)
                logo.save(save_path)
                logo_path = os.path.join("uploads", "logos", filename).replace("\\", "/")  # <-- FIX HERE


        password_hash = generate_password_hash(password)

        # MySQL insert
        cursor.execute("""
            INSERT INTO companies (company_name, gst_number, address, phone, email, description, password_hash, logo_path)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (company_name, gst_number, address, phone, email, description, password_hash, logo_path))
        conn.commit()

        # CSV insert
        with open("company_data.csv", "a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([company_name, gst_number, address, phone, email, description, password_hash, logo_path])

        return redirect("/login")

    return render_template("register.html")


from flask import request, session, redirect, url_for, render_template, flash
from werkzeug.security import generate_password_hash, check_password_hash

# @app.route("/edit_profile", methods=["GET", "POST"])
# def edit_profile():
#     if "company_id" not in session:
#         return redirect(url_for("login"))

#     company_id = session["company_id"]
#     conn = mysql.connector.connect(**db_config)
#     cursor = conn.cursor(dictionary=True)

#     if request.method == "POST":
#         # Get form inputs
#         old_password = request.form.get("old_password")
#         new_password = request.form.get("new_password")

#         # Fetch current password hash from database
#         cursor.execute("SELECT password_hash FROM companies WHERE id = %s", (company_id,))
#         result = cursor.fetchone()

#         if result and check_password_hash(result["password_hash"], old_password):
#             if new_password.strip():
#                 new_hash = generate_password_hash(new_password)
#                 cursor.execute("UPDATE companies SET password_hash = %s WHERE id = %s", (new_hash, company_id))
#                 conn.commit()
#                 flash("Password updated successfully!", "success")
#             else:
#                 flash("New password cannot be empty.", "warning")
#         else:
#             flash("Old password is incorrect.", "danger")

#     # Reload current profile for form
#     cursor.execute("SELECT * FROM companies WHERE id = %s", (company_id,))
#     company = cursor.fetchone()

#     cursor.close()
#     conn.close()

#     return render_template("edit_profile.html", company=company)


@app.route("/edit_profile", methods=["GET", "POST"])
def edit_profile():
    if "company_id" not in session:
        return redirect(url_for("login"))

    company_id = session["company_id"]
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":
        action = request.form.get("action")

        if action == "update_info":
            # Update company profile info
            company_name = request.form.get("company_name")
            gst_number = request.form.get("gst_number")
            address = request.form.get("address")
            phone = request.form.get("phone")
            email = request.form.get("email")
            description = request.form.get("description")

            cursor.execute("""
                UPDATE companies
                SET company_name = %s, gst_number = %s, address = %s,
                    phone = %s, email = %s, description = %s
                WHERE id = %s
            """, (company_name, gst_number, address, phone, email, description, company_id))
            conn.commit()
            flash("Company profile updated successfully.", "success")

        elif action == "update_password":
            # Update password only
            old_password = request.form.get("old_password")
            new_password = request.form.get("new_password")

            cursor.execute("SELECT password_hash FROM companies WHERE id = %s", (company_id,))
            result = cursor.fetchone()

            if result and result["password_hash"] and check_password_hash(result["password_hash"], old_password):
                if new_password.strip():
                    new_hash = generate_password_hash(new_password)
                    cursor.execute("UPDATE companies SET password_hash = %s WHERE id = %s", (new_hash, company_id))
                    conn.commit()
                    flash("Password updated successfully!", "success")
                else:
                    flash("New password cannot be empty.", "warning")
            else:
                flash("Old password is incorrect.", "danger")

    # Load company info for form display
    cursor.execute("SELECT * FROM companies WHERE id = %s", (company_id,))
    company = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template("edit_profile.html", company=company)





# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     message = request.args.get('message')
#     if request.method == 'POST':
#         company_name = request.form['company_name'].strip()
#         password = request.form['password']

#         if not company_name or not password:
#             return render_template('login.html', error='Company Name and Password are required.')

#         user_data = get_user_data(company_name)

#         if user_data and check_password_hash(user_data['Password Hash'], password):
#             session['company_name'] = company_name
#             return redirect(url_for('index'))
#         else:
#             return render_template('login.html', error='Invalid Company Name or Password.')
#     return render_template('login.html', message=message)
from werkzeug.security import check_password_hash

# @app.route("/login", methods=["GET", "POST"])
# def login():
#     if request.method == "POST":
#         email = request.form.get("email")
#         password = request.form.get("password")

#         if not email or not password:
#             return "Email and password required", 400

#         cursor.execute("SELECT password_hash FROM companies WHERE email = %s", (email,))
#         result = cursor.fetchone()

#         if result and check_password_hash(result[0], password):
#             return redirect("/index")
#         else:
#             return "Invalid email or password", 401

#     return render_template("login.html")
# @app.route("/login", methods=["GET", "POST"])
# def login():
#     if request.method == "POST":
#         email = request.form["email"]
#         password = request.form["password"]

#         cursor.execute("SELECT id, company_name, password_hash FROM companies WHERE email = %s", (email,))
#         result = cursor.fetchone()

#         print("Login Attempt:", email)
#         print("Query Result:", result)

#         if result:
#             user_id, company_name, password_hash = result
#             if check_password_hash(password_hash, password):
#                 session["user_id"] = user_id
#                 session["company_name"] = company_name
#                 return redirect(url_for('index'))  # or your actual dashboard route
#             else:
#                 print("Invalid password")
#         else:
#             print("Email not found")

#         return "Invalid email or password", 401

#     return render_template("login.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        cursor.execute("SELECT id, company_name, password_hash FROM companies WHERE email = %s", (email,))
        result = cursor.fetchone()

        if result:
            user_id, company_name, password_hash = result
            if check_password_hash(password_hash, password):
                session["user_id"] = user_id
                session["company_id"] = user_id  # ✅ IMPORTANT LINE
                session["company_name"] = company_name
                return redirect(url_for('index'))  # or your dashboard
            else:
                print("Invalid password")
        else:
            print("Email not found")

        return "Invalid email or password", 401

    return render_template("login.html")



# @app.route('/logout')
# def logout():
#     session.pop('company_name', None)
#     return redirect(url_for('index'))
# @app.route('/logout')
# def logout():
#     session.clear()  # Clear all session data safely
#     return redirect(url_for('login'))  # Redirect to login page
from flask import flash

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out successfully.", "info")
    return redirect(url_for('index'))

# @app.route('/profile', methods=['GET', 'POST'])
# @login_required
# def profile():
#     if g.user is None:
#         return redirect(url_for('login')) # Should not happen due to @login_required

#     current_user_data = g.user.copy() # Use a copy to avoid modifying g.user directly during template rendering

#     if request.method == 'POST':
#         # Get updated data from form
#         updated_company_name = request.form['company_name'].strip()
#         updated_gst_number = request.form['gst_number'].strip()
#         updated_address = request.form['address'].strip()
#         updated_phone = request.form['phone'].strip()
#         updated_email = request.form['email'].strip()
#         updated_description = request.form['description'].strip()
#         new_password = request.form.get('new_password', '').strip()
#         confirm_new_password = request.form.get('confirm_new_password', '').strip()

#         users = get_all_users_data()
#         updated_users = []
#         profile_updated = False
#         error = None

#         for user in users:
#             if user['Company Name'] == session['company_name']: # Found the current user
#                 # Check if company name is being changed and if new name exists
#                 if updated_company_name.lower() != session['company_name'].lower():
#                     # Check if new company name already exists for another user
#                     if any(u['Company Name'].lower() == updated_company_name.lower() and u['Company Name'] != session['company_name'] for u in users):
#                         error = 'New Company Name already taken by another user.'
#                         updated_users.append(user) # Add original user data back
#                         break # Exit loop, don't save
#                     user['Company Name'] = updated_company_name
#                     # Update session if company name changed
#                     session['company_name'] = updated_company_name

#                 user['GST Number'] = updated_gst_number
#                 user['Address'] = updated_address
#                 user['Phone'] = updated_phone
#                 user['Email'] = updated_email
#                 user['Description'] = updated_description
#                 updated_description = request.form['description'].strip()
#                 if new_password:
#                     if new_password != confirm_new_password:
#                         error = 'New passwords do not match.'
#                         updated_users.append(user) # Add current user data back
#                         break
#                     user['Password Hash'] = generate_password_hash(new_password)
#                 profile_updated = True
#                 updated_users.append(user)
#             else:
#                 updated_users.append(user)

#         if error:
#             # Re-render profile with error message and original data (or partially updated)
#             return render_template('profile.html', user=current_user_data, error=error)

#         if profile_updated:
#             try:
#                 with open(PROFILE_CSV_FILE, 'w', newline='', encoding='utf-8') as csvfile:
#                     writer = csv.DictWriter(csvfile, fieldnames=PROFILE_HEADERS)
#                     writer.writeheader()
#                     writer.writerows(updated_users)
#                 # Update g.user with the latest data after saving
#                 g.user = get_user_data(session['company_name'])
#                 return render_template('profile.html', user=g.user, success='Profile updated successfully!')
#             except Exception as e:
#                 app.logger.error(f"Error updating profile for {session['company_name']}: {e}")
#                 return render_template('profile.html', user=current_user_data, error=f'Failed to update profile: {str(e)}')
#         else:
#             return render_template('profile.html', user=current_user_data, error='No changes detected or user not found.')

#     return render_template('profile.html', user=current_user_data)

# @app.route("/profile", methods=["GET", "POST"])
# def profile():
#     if "user_id" not in session:
#         return redirect(url_for("login"))

#     user_id = session["user_id"]

#     cursor.execute("""
#         SELECT company_name, gst_number, address, phone, email, description, logo_path
#         FROM companies
#         WHERE id = %s
#     """, (user_id,))
    
#     result = cursor.fetchone()

#     if not result:
#         return "Company not found", 404

#     company = {
#         "company_name": result[0],
#         "gst_number": result[1],
#         "address": result[2],
#         "phone": result[3],
#         "email": result[4],
#         "description": result[5],
#         # "logo_path": result[6]
#         "logo_path": result[6].replace("\\", "/")  # ✅ important fix here

#     }

#     return render_template("profile.html", company=company)


@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect('/login')

    user_id = session['user_id']

    # conn = mysql.connector.connect(
    #     host='localhost',
    #     user='root',
    #     password='Rit420@$',
    #     database='challan'
    # )
    conn = mysql.connector.connect(
        host="sql12.freesqldatabase.com",
        user="sql12793850",
        password="XtmBdMHs8T",
        database="sql12793850",
        port=3306
    )
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM companies WHERE id = %s", (user_id,))
    company = cursor.fetchone()

    cursor.close()
    conn.close()

    if not company:
        return "Company profile not found", 404

    return render_template('profile.html', company=company)





# Import request and jsonify if not already imported
from flask import request, jsonify, render_template, session, g # Ensure render_template is imported



@app.route('/preview_invoice', methods=['POST'])
@login_required # Ensure user is logged in
def preview_invoice():
    """
    Receives invoice data and selected theme, then renders a preview.
    """
    invoice_data = request.json # Data sent from frontend
    selected_theme = invoice_data.get('selectedTheme', 'basic') # Default to 'basic'

    print(f"Received data for theme '{selected_theme}':")
    print(json.dumps(invoice_data, indent=2)) # Pretty print the received data

   
    # Example: Dynamic template selection
    theme_template_map = {
        'basic': 'themes/basic_invoice_preview.html',
        'modern': 'themes/modern_invoice_preview.html',
        'corporate': 'themes/corporate_invoice_preview.html',
        'minimal': 'themes/basic_invoice_preview.html', # Fallback for now
        'classic': 'themes/basic_invoice_preview.html', # Fallback for now
        'red-accent': 'themes/basic_invoice_preview.html', # Fallback for now
        'green-minimal': 'themes/basic_invoice_preview.html', # Fallback for now
        'dark-mode-lite': 'themes/basic_invoice_preview.html', # Fallback for now
        'invoice-pro': 'themes/basic_invoice_preview.html', # Fallback for now
        'elegant-lines': 'themes/basic_invoice_preview.html', # Fallback for now
        # Add more mappings as you create new theme templates
    }
    
    template_to_render = theme_template_map.get(selected_theme, 'themes/basic_invoice_preview.html')


    # You will need to create these theme-specific HTML files in your 'templates/themes/' folder.
    # For now, let's just make a very basic `basic_invoice_preview.html` to get it working.
    
    # Pass all collected invoice data to the template
    return render_template(template_to_render, invoice=invoice_data)


# app = Flask(__name__)
from flask import Flask, render_template, request
from num2words import num2words

# @app.route("/preview_invoice/<theme>", methods=["POST"])
# def preview_invoice_with_theme(theme):
#     from num2words import num2words

#     # Sender (company) details
#     company_name = request.form.get("company_name", "").strip()
#     company_address = request.form.get("company_address", "").strip()
#     company_email = request.form.get("company_email", "").strip()
#     company_phone = request.form.get("company_phone", "").strip()
#     company_gstin = request.form.get("company_gstin", "").strip()
#     company_description = request.form.get("company_description", "").strip()

#     # Receiver details
#     customer = request.form.get("customer", "").strip()
#     gst_number = request.form.get("gst_number", "").strip()
#     invoice_number = request.form.get("invoice_number", "").strip()
#     invoice_date = request.form.get("invoice_date", "").strip()

#     # Product fields
#     descriptions = request.form.getlist("description[]")
#     hsns = request.form.getlist("hsn[]")
#     quantities = request.form.getlist("quantity[]")
#     units = request.form.getlist("unit[]")
#     rates = request.form.getlist("rate[]")

#     items = []
#     total_amount = 0.0

#     for desc, hsn, qty, unit, rate in zip(descriptions, hsns, quantities, units, rates):
#         if not desc.strip():
#             continue
#         try:
#             qty = float(qty)
#             rate = float(rate)
#             total = qty * rate
#         except:
#             qty = 0
#             rate = 0
#             total = 0
#         items.append({
#             "description": desc,
#             "hsn": hsn,
#             "quantity": qty,
#             "unit": unit,
#             "rate": rate,
#             "total": total
#         })
#         total_amount += total

#     total_in_words = num2words(total_amount, to='currency', lang='en_IN').upper()

#     return render_template(
#         f"themes/{theme}.html",
#         company_name=company_name,
#         company_address=company_address,
#         company_email=company_email,
#         company_phone=company_phone,
#         company_gstin=company_gstin,
#         company_description=company_description,
#         customer=customer,
#         gst_number=gst_number,
#         invoice_number=invoice_number,
#         invoice_date=invoice_date,
#         items=items,
#         total_amount=total_amount,
#         total_in_words=total_in_words
#     )
@app.route("/preview_invoice/<theme>", methods=["POST"])
def preview_invoice_with_theme(theme):
    from num2words import num2words
    import mysql.connector

    # Sender details
    company_name = request.form.get("company_name", "").strip()
    company_gstin = request.form.get("company_gstin", "").strip()
    company_address = request.form.get("company_address", "").strip()
    company_phone = request.form.get("company_phone", "").strip()
    company_email = request.form.get("company_email", "").strip()
    company_description = request.form.get("company_description", "").strip()
    logo_path = request.form.get("logo_path", "").strip()
    logo_path = g.user.get('Logo Path', '')  # Assuming this is where it's stored

    # Receiver basic
    customer = request.form.get("customer", "").strip()
    gst_number = request.form.get("gst_number", "").strip()

    # Try to fetch full receiver details from DB
    receiver_address = receiver_phone = receiver_email = transport = vehicle_no = ""

    # conn = mysql.connector.connect(
    #     host="localhost",
    #     user="root",
    #     password="Rit420@$",
    #     database="challan"
    # )
    conn = mysql.connector.connect(
        host="sql12.freesqldatabase.com",
        user="sql12793850",
        password="XtmBdMHs8T",
        database="sql12793850",
        port=3306
    )
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM receivers WHERE company_name = %s", (customer,))
    receiver = cursor.fetchone()
    conn.close()

    if receiver:
        receiver_address = receiver["address"]
        receiver_phone = receiver["phone"]
        receiver_email = receiver["email"]
        gst_number = receiver["gst_number"]

    # Invoice details
    invoice_number = request.form.get("invoice_number", "").strip()
    invoice_date = request.form.get("invoice_date", "").strip()

    # Products
    descriptions = request.form.getlist("description[]")
    hsns = request.form.getlist("hsn[]")
    quantities = request.form.getlist("quantity[]")
    units = request.form.getlist("unit[]")
    rates = request.form.getlist("rate[]")

    items = []
    total_amount = 0.0

    for desc, hsn, qty, unit, rate in zip(descriptions, hsns, quantities, units, rates):
        if not desc.strip():
            continue
        try:
            qty = float(qty)
            rate = float(rate)
            total = qty * rate
        except:
            qty = rate = total = 0.0

        items.append({
            "description": desc,
            "hsn": hsn,
            "quantity": qty,
            "unit": unit,
            "rate": rate,
            "total": total
        })
        total_amount += total

    total_in_words = num2words(total_amount, to='currency', lang='en_IN').upper()

    return render_template(
        f"themes/{theme}.html",
        company_name=company_name,
        company_address=company_address,
        company_email=company_email,
        company_phone=company_phone,
        company_gstin=company_gstin,
        company_description=company_description,
        logo_path=logo_path,
        customer=customer,
        gst_number=gst_number,
        receiver_address=receiver_address,
        receiver_phone=receiver_phone,
        receiver_email=receiver_email,
        transport=transport,
        vehicle_no=vehicle_no,
        invoice_number=invoice_number,
        invoice_date=invoice_date,
        items=items,
        total_amount=total_amount,
        total_in_words=total_in_words
    )

import json # Make sure this is imported if not already


# ... (your existing routes like index, add_challan, company_view, generate_invoice, save_challan, etc.) ...
@app.route('/generate_delivery_challan')
@login_required # Ensure user is logged in to access this page
def generate_delivery_challan():
    if not g.user:
        return redirect(url_for('login')) # Redirect to login if not authenticated

    # Pass the logged-in user's company details as sender_details
    return render_template('generate_delivery_challan.html', sender_details=g.user)



@app.route('/save_delivery_challan', methods=['POST'])
@login_required
def save_delivery_challan():
    if not request.is_json:
        return jsonify({"message": "Request must be JSON"}), 400

    data = request.get_json()

    # Receiver details
    company_name = data.get('companyName')
    gst_number = data.get('gstNumber')
    challan_date = data.get('challanDate')
    challan_number = data.get('challanNumber')
    products = data.get('products', [])

    # Sender details (from hidden inputs in the form)
    sender_company_name = data.get('sender_company_name')
    sender_company_gstin = data.get('sender_company_gstin')
    sender_company_address = data.get('sender_company_address')
    sender_company_phone = data.get('sender_company_phone')
    sender_company_email = data.get('sender_company_email')
    sender_company_description = data.get('sender_company_description')


    if not all([company_name, challan_date, challan_number]):
        return jsonify({"message": "Missing required delivery challan details (Company Name, Challan Date, Challan Number)."}), 400

    # Sanitize company name for filename (for the receiver's challan file)
    sanitized_company_name = re.sub(r'[^\w\s-]', '', company_name).strip().replace(' ', '_')
    csv_filename = os.path.join(CSV_FOLDER, f"{sanitized_company_name}_delivery_challans.csv") # Using a distinct filename

    # Define CSV header for Delivery Challan
    fieldnames = [
        'Sender Company Name', 'Sender GST Number', 'Sender Address', 'Sender Phone', 'Sender Email', 'Sender Description',
        'Receiver Company Name', 'Receiver GST Number', 'Challan Date', 'Challan Number',
        'Product Description', 'HSN Code', 'Quantity', 'Weight', 'Challan No.' # Updated fields
    ]

    file_exists = os.path.exists(csv_filename)

    try:
        with open(csv_filename, 'a' if file_exists else 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            if not file_exists:
                writer.writeheader() # Write header only if file is new

            for product in products:
                row = {
                    'Sender Company Name': sender_company_name,
                    'Sender GST Number': sender_company_gstin,
                    'Sender Address': sender_company_address,
                    'Sender Phone': sender_company_phone,
                    'Sender Email': sender_company_email,
                    'Sender Description': sender_company_description,
                    'Receiver Company Name': company_name,
                    'Receiver GST Number': gst_number, # This might be empty if not fetched/entered
                    'Challan Date': challan_date,
                    'Challan Number': challan_number,
                    'Product Description': product.get('description', ''),
                    'HSN Code': product.get('hsn', ''),
                    'Quantity': product.get('quantity', ''),
                    'Weight': product.get('weight', ''), # Corresponds to 'Weight'
                    'Challan No.': product.get('challan_no', '') # Corresponds to 'Challan No.'
                }
                writer.writerow(row)

        return jsonify({"message": f"Delivery Challan saved successfully for {company_name}!"}), 200

    except Exception as e:
        app.logger.error(f"Error saving delivery challan data to CSV for {company_name}: {e}")
        return jsonify({"message": f"Failed to save delivery challan: {str(e)}"}), 500


from flask import Flask, render_template, request, jsonify, redirect, url_for, session, g, send_from_directory
# ... rest of your imports
# --- New: Directory for Generated Challan HTML Files ---
CHALLAN_HTML_FOLDER = 'delivery_challans'
if not os.path.exists(CHALLAN_HTML_FOLDER):
    os.makedirs(CHALLAN_HTML_FOLDER)
# --- New Route: Generate Challan HTML ---
# @app.route('/generate_challan_html', methods=['POST'])
# @login_required
# def generate_challan_html():
#     data = request.get_json()
#     format_key = data.get('format', 'format1') # Default to format1 if not specified
#     challan_number = data.get('challanNumber', 'UNKNOWN_CHALLAN')
#     receiver_company_name = data.get('companyName', 'UNKNOWN_RECEIVER').replace(' ', '_') # For filename

#     # Prepare data for template rendering (using the keys as used in your HTML templates)
#     challan_data = {
#         'sender_details': {
#             'Company Name': data.get('sender_company_name'),
#             'GST Number': data.get('sender_company_gstin'),
#             'Address': data.get('sender_company_address'),
#             'Phone': data.get('sender_company_phone'),
#             'Email': data.get('sender_company_email'),
#             'Description': data.get('sender_company_description'),
#             'Logo Path': g.user.get('Logo Path', '')
#         },
#         # 'receiver_details': {
#         #     'Company Name': data.get('companyName'),
#         #     'GST Number': data.get('gstNumber')
#         # },
#         'receiver_details': {
#             'Company Name': data.get('companyName'),
#             'GST Number': data.get('gstNumber'),
#             'Address': data.get('address', ''),
#             'Phone': data.get('phone', ''),
#             'Email': data.get('email', ''),
#             'Transport': data.get('transport', ''),
#             'Vehicle No': data.get('vehicle_no', '')
#         },

#         'challan_info': {
#             'date': data.get('challanDate'),
#             'number': challan_number
#         },
#         'products': data.get('products', [])
#     }
#     print(f"DEBUG: Sender Details being passed to template: {challan_data['sender_details']}") # ADD THIS LINE this is changed one

#     # Map format keys to template filenames
#     template_map = {
#         'format1': 'challan_format_1.html',
#         'format2': 'challan_format_2.html',
#         'format3': 'challan_format_3.html',
#         'format4': 'challan_format_4.html',
#     }
#     print("DEBUG receiver address:", data.get('address'))

#     template_name = template_map.get(format_key, 'challan_format_1.html') # Fallback to format1

#     try:
#         # Render the specific challan template with the data
#         rendered_html = render_template(template_name, **challan_data)

#         # Generate a unique and safe filename for the generated HTML
#         # Using receiver company name, challan number, and format key
#         filename = f"{receiver_company_name}_{challan_number}_{format_key}.html"
#         # Sanitize filename further if necessary (e.g., remove special chars)
#         filename = re.sub(r'[^\w\s.-]', '', filename).strip().replace(' ', '_')
#         filepath = os.path.join(CHALLAN_HTML_FOLDER, filename)

#         # Save the rendered HTML to the file system
#         with open(filepath, 'w', encoding='utf-8') as f:
#             f.write(rendered_html)

#         # Return the URL to the newly created file
#         # This uses the new route '/delivery_challans/<filename>'
#         challan_url = url_for('serve_challan_html', filename=filename)
#         return jsonify({"message": "Challan HTML generated successfully!", "status": "success", "challan_url": challan_url}), 200

#     except Exception as e:
#         app.logger.error(f"Error generating challan HTML for format {format_key}: {e}")
#         return jsonify({"message": f"Failed to generate challan HTML: {str(e)}", "status": "error"}), 500
import mysql.connector

def get_receiver_details(receiver_id):
    try:
        # connection = mysql.connector.connect(
        #     host='localhost',
        #     user='root',
        #     password='Rit420@$',
        #     database='challan'
        # )
        conn = mysql.connector.connect(
            host="sql12.freesqldatabase.com",
            user="sql12793850",
            password="XtmBdMHs8T",
            database="sql12793850",
            port=3306
        )
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM receiver WHERE id = %s", (receiver_id,))
        receiver = cursor.fetchone()
        cursor.close()
        connection.close()
        return receiver
    except Exception as e:
        print(f"Error fetching receiver details from DB: {e}")
        return None

@app.route('/generate_challan_html', methods=['POST'])
@login_required
def generate_challan_html():
    data = request.get_json()
    format_key = data.get('format', 'format1')
    challan_number = data.get('challanNumber', 'UNKNOWN_CHALLAN')
    receiver_company_name = data.get('companyName', 'UNKNOWN_RECEIVER').replace(' ', '_')

    # ✅ Fetch receiver details from MySQL using company name or ID
    # receiver_details = {}
    # try:
    #     company_name = data.get('companyName')
    #     cursor = mysql.connection.cursor(dictionary=True)
    #     cursor.execute("SELECT * FROM receivers WHERE `Company Name` = %s", (company_name,))
    #     receiver_details = cursor.fetchone() or {}

    #     cursor.close()
    # except Exception as e:
    #     app.logger.error(f"Error fetching receiver details from DB: {e}")
    #     return jsonify({"message": f"Database error while fetching receiver: {str(e)}", "status": "error"}), 500
    # ✅ Fetch receiver details from MySQL using company name
    receiver_details = {}
    try:
        company_name = data.get('companyName')
        # connection = mysql.connector.connect(
        #     host='localhost',
        #     user='root',
        #     password='Rit420@$',
        #     database='challan'
        # )
        conn = mysql.connector.connect(
            host="sql12.freesqldatabase.com",
            user="sql12793850",
            password="XtmBdMHs8T",
            database="sql12793850",
            port=3306
        )
        cursor = connection.cursor(dictionary=True)
        # cursor.execute("SELECT * FROM receivers WHERE `Company Name` = %s", (company_name,))
        cursor.execute("SELECT * FROM receivers WHERE company_name = %s", (company_name,))

        receiver_details = cursor.fetchone() or {}
        print("Fetched receiver details:", receiver_details)
        cursor.close()
        connection.close()
    except Exception as e:
        app.logger.error(f"Error fetching receiver details from DB: {e}")
        return jsonify({"message": f"Database error while fetching receiver: {str(e)}", "status": "error"}), 500

        # ✅ Fill challan data
    challan_data = {
        'sender_details': {
            'Company Name': data.get('sender_company_name'),
            'GST Number': data.get('sender_company_gstin'),
            'Address': data.get('sender_company_address'),
            'Phone': data.get('sender_company_phone'),
            'Email': data.get('sender_company_email'),
            'Description': data.get('sender_company_description'),
            'Logo Path': g.user.get('Logo Path', '')
        },
        'receiver_details': {
            'Company Name': receiver_details.get('company_name', ''),
            'GST Number': receiver_details.get('gst_number', ''),
            'Address': receiver_details.get('address', ''),
            'Phone': receiver_details.get('phone', ''),
            'Email': receiver_details.get('email', ''),
            'Transport': receiver_details.get('Transport', ''),
            'Vehicle No': receiver_details.get('Vehicle No', '')
        },
        'challan_info': {
            'date': data.get('challanDate'),
            'number': challan_number
        },
        'products': data.get('products', [])
    }

    # Template selection
    template_map = {
        'format1': 'challan_format_1.html',
        'format2': 'challan_format_2.html',
        'format3': 'challan_format_3.html',
        'format4': 'challan_format_4.html',
    }
    template_name = template_map.get(format_key, 'challan_format_1.html')

    try:
        # Render HTML and save
        rendered_html = render_template(template_name, **challan_data)
        filename = f"{receiver_company_name}_{challan_number}_{format_key}.html"
        filename = re.sub(r'[^\w\s.-]', '', filename).strip().replace(' ', '_')
        filepath = os.path.join(CHALLAN_HTML_FOLDER, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(rendered_html)

        challan_url = url_for('serve_challan_html', filename=filename)
        return jsonify({"message": "Challan HTML generated successfully!", "status": "success", "challan_url": challan_url}), 200

    except Exception as e:
        app.logger.error(f"Error generating challan HTML for format {format_key}: {e}")
        return jsonify({"message": f"Failed to generate challan HTML: {str(e)}", "status": "error"}), 500

# --- New Route: Serve Generated Challan HTML Files ---
@app.route('/delivery_challans/<filename>')
def serve_challan_html(filename):
    """
    Serves the static challan HTML files from the CHALLAN_HTML_FOLDER.
    Note: For production, consider using a proper web server (e.g., Nginx, Apache) to serve static files.
    """
    return send_from_directory(CHALLAN_HTML_FOLDER, filename)

from werkzeug.utils import secure_filename

@app.route('/upload_logo', methods=['POST'])
@login_required # Ensure only logged-in users can upload
def upload_logo():
    if 'logo_file' not in request.files:
        return jsonify({"message": "No file part"}), 400
    file = request.files['logo_file']
    if file.filename == '':
        return jsonify({"message": "No selected file"}), 400
    if file and allowed_file(file.filename):
        username = g.user['username'] # Assuming user identity is stored in g.user
        filename = secure_filename(f"{username}_logo.{file.filename.rsplit('.', 1)[1].lower()}")
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Update the user's profile with the new logo path
        profiles = []
        with open(PROFILE_CSV_FILE, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                profiles.append(row)

        updated = False
        with open(PROFILE_CSV_FILE, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=PROFILE_HEADERS)
            writer.writeheader()
            for row in profiles:
                if row.get('Company Name') == username: # Or whatever unique identifier you use
                    row['Logo Path'] = filename
                    updated = True
                writer.writerow(row)
        if updated:
            return jsonify({"message": "Logo uploaded successfully!", "logo_path": filename}), 200
        else:
            return jsonify({"message": "User profile not found to update logo."}), 404
    return jsonify({"message": "File type not allowed"}), 400

if __name__ == '__main__':
    app.run(debug=True) 
