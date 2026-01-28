from flask import Flask, request, jsonify, session, render_template
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta, date
import os
from functools import wraps
import re
import requests
import traceback
from dotenv import load_dotenv
from urllib.parse import quote_plus

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')

DB_USERNAME = os.environ.get('DB_USERNAME', 'root')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'password')
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = os.environ.get('DB_PORT', '3306')
DB_NAME = os.environ.get('DB_NAME', 'AgriSafe')

encoded_password = quote_plus(DB_PASSWORD)
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{DB_USERNAME}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# WhatsApp Configuration
WHATSAPP_API_URL = os.environ.get('WHATSAPP_API_URL', 'https://api.tryowbot.com/sender')
WHATSAPP_API_TOKEN = os.environ.get('WHATSAPP_API_TOKEN', 'fKyd6nTfOloQt5gpyBMIwDq7S1tNtk4xeGtH5LK18a569deb')
WHATSAPP_TIMEOUT = int(os.environ.get('WHATSAPP_TIMEOUT', '30'))
WHATSAPP_MAX_RETRIES = int(os.environ.get('WHATSAPP_MAX_RETRIES', '3'))
WHATSAPP_ENABLED = os.environ.get('WHATSAPP_ENABLED', 'true').lower() == 'true'

# Import database operations from separate db.py file
import db as database
from db import (
    get_medical_shop_by_mobile, get_medical_shop_by_id, create_medical_shop,
    get_farmer_by_id, create_farmer, get_doctor_by_id, create_doctor,
    get_recommendation_by_id, get_recommendations_by_shop_id, claim_recommendation,
    get_recommendation_items_by_recommendation_id, create_recommendation_item,
    update_recommendation_item_dates, get_shop_statistics, search_unclaimed_recommendations,
    test_database_connection
)

# Database operations now use raw SQL queries through db.py module
# No SQLAlchemy models needed - all operations are SQL-based

def send_whatsapp_message(farmer_mobile, farmer_name, recommendation_items, start_date, end_date):
    """
    Send WhatsApp message to farmer with antibiotic recommendations
    """
    try:
        app.logger.info(f"DEBUG: Starting WhatsApp message preparation for farmer: {farmer_name}")
        app.logger.info(f"DEBUG: Input types - start_date: {type(start_date)}, end_date: {type(end_date)}")
        app.logger.info(f"DEBUG: Input values - start_date: {start_date}, end_date: {end_date}")
        
        # Clean up mobile number (remove any non-numeric characters except +)
        mobile = re.sub(r'[^\d+]', '', farmer_mobile)
        if mobile.startswith('+'):
            mobile = mobile[1:]  # Remove + sign
        
        app.logger.info(f"DEBUG: Cleaned mobile number: {mobile}")
        
        # Prepare antibiotic information
        antibiotics_info = []
        total_dosages = []
        
        app.logger.info(f"DEBUG: Processing {len(recommendation_items)} recommendation items")
        
        for i, item in enumerate(recommendation_items):
            app.logger.info(f"DEBUG: Item {i+1} - antibiotic: {item['antibiotic_name']}, dosage: {item['total_daily_dosage_ml']}ml, frequency: {item['daily_frequency']}")
            
            antibiotic_info = f"{item['antibiotic_name']}"
            dosage_info = f"{item['total_daily_dosage_ml']}ml"
            frequency_info = f"{item['daily_frequency']} times daily"
            
            antibiotics_info.append(antibiotic_info)
            total_dosages.append(dosage_info)
        
        # Concatenate multiple antibiotics
        medicine_names = ", ".join(antibiotics_info)
        dosage_details = ", ".join(total_dosages)
        
        # Get frequency from first item (assuming similar frequency for all)
        frequency = str(recommendation_items[0]['daily_frequency']) if recommendation_items else "1"
        
        app.logger.info(f"DEBUG: Combined medicines: {medicine_names}")
        app.logger.info(f"DEBUG: Combined dosages: {dosage_details}")
        app.logger.info(f"DEBUG: Frequency: {frequency}")
        
        # Format dates - handle both datetime.date and datetime.datetime objects
        if hasattr(start_date, 'strftime'):
            from_date = start_date.strftime("%d/%m/%Y")
        else:
            from_date = str(start_date)
            
        if hasattr(end_date, 'strftime'):
            to_date = end_date.strftime("%d/%m/%Y")
        else:
            to_date = str(end_date)
        
        app.logger.info(f"DEBUG: Formatted dates - from: {from_date}, to: {to_date}")
        
        # Prepare payload for TryOwBot API
        payload = {
            "token": WHATSAPP_API_TOKEN,
            "phone": mobile,
            "template_name": "agri_safe",
            "template_language": "en",
            "text1": str(farmer_name),      # {{1}} Farmer Name
            "text2": str(medicine_names),   # {{2}} Medicine names (concatenated)
            "text3": str(dosage_details),   # {{3}} Dosage details (concatenated)
            "text4": str(frequency),        # {{4}} Frequency
            "text5": str(from_date),        # {{5}} From Date
            "text6": str(to_date)           # {{6}} To Date
        }
        
        app.logger.info(f"DEBUG: WhatsApp payload prepared: {payload}")
        
        headers = {"Content-Type": "application/json"}
        
        # Send WhatsApp message with retry logic
        app.logger.info(f"DEBUG: Sending WhatsApp request to {WHATSAPP_API_URL}")
        
        # Check if WhatsApp is enabled
        if not WHATSAPP_ENABLED:
            app.logger.info("WhatsApp messaging is disabled")
            return False, "WhatsApp messaging is disabled in configuration"
        
        # Configure timeouts and retry attempts from environment
        max_retries = WHATSAPP_MAX_RETRIES
        timeout_seconds = WHATSAPP_TIMEOUT
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                app.logger.info(f"DEBUG: WhatsApp API attempt {attempt + 1}/{max_retries}")
                
                # Make request with longer timeout
                response = requests.post(
                    WHATSAPP_API_URL, 
                    headers=headers, 
                    json=payload, 
                    timeout=timeout_seconds
                )
                
                app.logger.info(f"DEBUG: WhatsApp API response status: {response.status_code}")
                app.logger.info(f"DEBUG: WhatsApp API response text: {response.text}")
                
                if response.status_code == 200:
                    app.logger.info(f"WhatsApp message sent successfully to {mobile} on attempt {attempt + 1}")
                    return True, f"WhatsApp message sent successfully (attempt {attempt + 1})"
                elif response.status_code == 429:  # Rate limit
                    app.logger.warning(f"Rate limit hit on attempt {attempt + 1}, will retry after delay")
                    if attempt < max_retries - 1:  # Don't sleep on last attempt
                        import time
                        time.sleep(retry_delay * 2)  # Longer delay for rate limits
                        continue
                else:
                    app.logger.error(f"Failed to send WhatsApp message: {response.status_code} - {response.text}")
                    return False, f"Failed to send WhatsApp message: HTTP {response.status_code}"
                    
            except requests.exceptions.Timeout as e:
                app.logger.warning(f"Timeout on attempt {attempt + 1}/{max_retries}: {str(e)}")
                if attempt < max_retries - 1:  # Don't sleep on last attempt
                    import time
                    time.sleep(retry_delay)
                    retry_delay *= 1.5  # Exponential backoff
                else:
                    app.logger.error(f"All WhatsApp API attempts failed due to timeout")
                    return False, f"WhatsApp API timeout after {max_retries} attempts"
                    
            except requests.exceptions.ConnectionError as e:
                app.logger.error(f"Connection error on attempt {attempt + 1}: {str(e)}")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(retry_delay)
                else:
                    return False, f"WhatsApp API connection failed after {max_retries} attempts"
            
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Request error while sending WhatsApp message: {str(e)}")
        return False, f"Network error: {str(e)}"
    except Exception as e:
        app.logger.error(f"Unexpected error while sending WhatsApp message: {str(e)}")
        import traceback
        app.logger.error(f"Full traceback: {traceback.format_exc()}")
        return False, f"Unexpected error: {str(e)}"

def check_whatsapp_api_health():
    """
    Check if WhatsApp API is reachable and responding
    """
    try:
        # Simple health check with minimal payload
        health_url = WHATSAPP_API_URL.replace('/sender', '/health') if '/sender' in WHATSAPP_API_URL else WHATSAPP_API_URL
        response = requests.get(health_url, timeout=5)
        return response.status_code < 500
    except:
        # If health endpoint doesn't exist, try a basic request with minimal timeout
        try:
            test_payload = {"token": "test"}
            response = requests.post(WHATSAPP_API_URL, json=test_payload, timeout=5)
            return True  # If we get any response, API is reachable
        except:
            return False

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'shop_id' not in session:
            # Check if this is an API request (expecting JSON)
            if request.path.startswith('/shop/') or request.path.startswith('/recommendations/'):
                return jsonify({'error': 'Login required', 'redirect': '/'}), 401
            # For HTML pages, redirect to home
            return render_template('index.html'), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    """Main page with login and signup"""
    return render_template('index.html')

@app.route('/admin')  
def admin_page():
    """Admin interface - original index page"""
    return render_template('index.html')

@app.route('/login')
def login_page():
    """Simple login page for testing"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Login</title>
        <style>
            body { font-family: Arial, sans-serif; padding: 50px; background: #f0f0f0; }
            .login-form { background: white; padding: 30px; border-radius: 10px; max-width: 400px; margin: 0 auto; }
            .btn { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }
            .btn:hover { background: #0056b3; }
            .form-group { margin: 15px 0; }
            input[type="text"] { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
        </style>
    </head>
    <body>
        <div class="login-form">
            <h2>Test Login</h2>
            <div class="form-group">
                <button class="btn" onclick="createTestSession()">Create Test Session</button>
            </div>
            <div id="message"></div>
        </div>
        
        <script>
            async function createTestSession() {
                try {
                    const response = await fetch('/test-login');
                    const result = await response.json();
                    
                    if (response.ok) {
                        document.getElementById('message').innerHTML = '<p style="color: green;">' + result.message + '</p>';
                        setTimeout(() => {
                            window.location.href = '/dashboard';
                        }, 1000);
                    } else {
                        document.getElementById('message').innerHTML = '<p style="color: red;">' + result.error + '</p>';
                    }
                } catch (error) {
                    document.getElementById('message').innerHTML = '<p style="color: red;">Error: ' + error.message + '</p>';
                }
            }
        </script>
    </body>
    </html>
    '''

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard_pro.html')

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logged out successfully'}), 200

@app.route('/search')
@login_required
def search_page():
    return render_template('search.html')

@app.route('/my-claims')
@login_required
def my_claims_page():
    return render_template('my_claims.html')

@app.route('/profile')
@login_required
def profile_page():
    return render_template('profile.html')

@app.route('/reports')
@login_required
def reports_page():
    return render_template('reports.html')

@app.route('/session-check')
def session_check():
    """Check current session status"""
    return jsonify({
        'session_exists': 'shop_id' in session,
        'shop_id': session.get('shop_id'),
        'shop_name': session.get('shop_name'),
        'session_keys': list(session.keys())
    })

@app.route('/shop/login', methods=['POST'])
def shop_login():
    try:
        data = request.get_json()
        if not data.get('mobile_no') or not data.get('password'):
            return jsonify({'error': 'Mobile number and password are required'}), 400
        
        shop = get_medical_shop_by_mobile(data['mobile_no'])
        
        if not shop or not check_password_hash(shop['password_hash'], data['password']):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        if not shop['is_active']:
            return jsonify({'error': 'Account is deactivated'}), 403
        
        session['shop_id'] = shop['id']
        session['shop_name'] = shop['shop_name']
        
        return jsonify({'message': 'Login successful'}), 200
        
    except Exception as e:
        return jsonify({'error': f'Login failed: {str(e)}'}), 500

@app.route('/shop/signup', methods=['POST'])
def shop_signup():
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['shop_name', 'owner_name', 'mobile_no', 'password', 
                          'license_number', 'pincode', 'address', 'city', 'state']
        
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field.replace("_", " ").title()} is required'}), 400
        
        # Check if mobile number already exists
        existing_shop = get_medical_shop_by_mobile(data['mobile_no'])
        if existing_shop:
            return jsonify({'error': 'Mobile number already registered'}), 409
        
        # Validate mobile number format (basic validation)
        if not re.match(r'^[+]?[1-9]\d{1,14}$', data['mobile_no']):
            return jsonify({'error': 'Invalid mobile number format'}), 400
        
        # Validate password strength (basic validation)
        if len(data['password']) < 6:
            return jsonify({'error': 'Password must be at least 6 characters long'}), 400
        
        # Prepare shop data
        shop_data = {
            'shop_name': data['shop_name'],
            'owner_name': data['owner_name'],
            'mobile_no': data['mobile_no'],
            'email': data.get('email'),
            'license_number': data['license_number'],
            'pincode': data['pincode'],
            'address': data['address'],
            'city': data['city'],
            'state': data['state'],
            'password_hash': generate_password_hash(data['password']),
            'is_verified': False,
            'is_active': True
        }
        
        # Create the medical shop
        shop_id = create_medical_shop(shop_data)
        
        return jsonify({
            'message': 'Medical shop registered successfully',
            'shop_id': shop_id
        }), 201
        
    except Exception as e:
        app.logger.error(f"Signup error: {str(e)}")
        app.logger.error(f"Full traceback: {traceback.format_exc()}")
        return jsonify({'error': f'Registration failed: {str(e)}'}), 500

@app.route('/shop/profile', methods=['GET'])
@login_required
def shop_profile():
    try:
        shop = get_medical_shop_by_id(session['shop_id'])
        if not shop:
            return jsonify({'error': 'Shop not found'}), 404
        
        return jsonify({
            'shop': {
                'id': shop['id'],
                'shop_name': shop['shop_name'],
                'owner_name': shop['owner_name'],
                'phone_number': shop['mobile_no'],  # Changed to match frontend
                'email': shop['email'],
                'license_number': shop['license_number'],
                'pincode': shop['pincode'],
                'address': shop['address'],
                'district': shop['city'],  # Changed to match frontend expectation
                'city': shop['city'],
                'state': shop['state'],
                'is_verified': shop['is_verified'],
                'is_active': shop['is_active'],
                'created_at': shop.get('created_at'),
                'specializations': shop.get('specializations', '')
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to fetch profile: {str(e)}'}), 500

@app.route('/shop/profile', methods=['PUT'])
@login_required
def update_shop_profile():
    try:
        data = request.get_json()
        shop_id = session['shop_id']
        
        # Update shop profile in database
        result = database.update_medical_shop_profile(shop_id, data)
        
        if result:
            return jsonify({'message': 'Profile updated successfully'}), 200
        else:
            return jsonify({'error': 'Failed to update profile'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Failed to update profile: {str(e)}'}), 500

@app.route('/shop/statistics', methods=['GET'])
@login_required  
def get_shop_statistics_route():
    try:
        shop_id = session['shop_id']
        print(f"Getting statistics for shop_id: {shop_id}")  # Debug log
        
        # Use the new SQL-based statistics function
        statistics = get_shop_statistics(shop_id)
        print(f"Statistics retrieved: {statistics}")  # Debug log
        
        return jsonify({
            'statistics': statistics
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to fetch statistics: {str(e)}'}), 500

@app.route('/shop/claimed-recommendations', methods=['GET'])
@login_required
def get_claimed_recommendations():
    try:
        shop_id = session['shop_id']
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        per_page = min(per_page, 50)
        
        # Get filter parameters
        from_date = request.args.get('from_date')
        to_date = request.args.get('to_date')
        animal_type = request.args.get('animal_type')
        
        # Prepare date filters for SQL query
        from_date_parsed = None
        to_date_parsed = None
        
        if from_date:
            try:
                from_date_parsed = datetime.strptime(from_date, '%Y-%m-%d').strftime('%Y-%m-%d %H:%M:%S')
            except ValueError:
                pass
                
        if to_date:
            try:
                to_date_obj = datetime.strptime(to_date, '%Y-%m-%d') + timedelta(days=1)
                to_date_parsed = to_date_obj.strftime('%Y-%m-%d %H:%M:%S')
            except ValueError:
                pass
        
        # Use new SQL-based function
        recommendations, total = get_recommendations_by_shop_id(
            shop_id=shop_id,
            page=page,
            per_page=per_page,
            from_date=from_date_parsed,
            to_date=to_date_parsed,
            animal_type=animal_type
        )
        
        # Process recommendations data
        recommendations_data = []
        for r in recommendations:
            # Get farmer and doctor data
            farmer = get_farmer_by_id(r['farmer_id'])
            doctor = get_doctor_by_id(r['doctor_id'])
            claimed_shop = get_medical_shop_by_id(r['claimed_by_shop_id']) if r['claimed_by_shop_id'] else None
            
            # Get real recommendation items from database
            recommendation_items = get_recommendation_items_by_recommendation_id(r['id'])
            
            # Convert items to API format
            items_data = []
            medicines_list = []
            for item in recommendation_items:
                if item['antibiotic_name'] and item['antibiotic_name'] != 'Placeholder - Update Required':
                    # Calculate total daily dosage
                    single_dose = item['single_dose_ml'] or 0
                    daily_freq = item['daily_frequency'] or 1
                    total_daily_dosage = single_dose * daily_freq
                    
                    item_data = {
                        'antibiotic_name': item['antibiotic_name'],
                        'disease': item['disease'] or 'Not specified',
                        'animal_type': item['animal_type'] or 'Not specified',
                        'weight': item['weight'] or 0,
                        'age': item['age'] or 0,
                        'single_dose_ml': single_dose,
                        'daily_frequency': daily_freq,
                        'treatment_days': item['treatment_days'] or 1,
                        'total_treatment_dosage_ml': item['total_treatment_dosage_ml'] or 0,
                        'total_daily_dosage_ml': total_daily_dosage,
                        'start_date': item['start_date'].isoformat() if item['start_date'] else None,
                        'end_date': item['end_date'].isoformat() if item['end_date'] else None
                    }
                    items_data.append(item_data)
                    medicines_list.append(item['antibiotic_name'])
            
            rec_data = {
                'id': r['id'],
                'farmer_id': r['farmer_id'],
                'doctor_id': r['doctor_id'],
                'is_claimed': r['is_claimed'],
                'claimed_by_shop_id': r['claimed_by_shop_id'],
                'claimed_at': r['claimed_at'].isoformat() if r['claimed_at'] else None,
                'claim_notes': r['claim_notes'],
                'claimed_by_shop': {
                    'id': claimed_shop['id'] if claimed_shop else None,
                    'shop_name': claimed_shop['shop_name'] if claimed_shop else None,
                    'owner_name': claimed_shop['owner_name'] if claimed_shop else None,
                    'mobile_no': claimed_shop['mobile_no'] if claimed_shop else None,
                    'address': claimed_shop['address'] if claimed_shop else None,
                    'pincode': claimed_shop['pincode'] if claimed_shop else None
                } if claimed_shop else None,
                'farmer': {
                    'name': farmer['name'] if farmer else f'Farmer {r["farmer_id"]}',
                    'mobile_no': farmer['mobile_no'] if farmer else f'N/A',
                    'area': farmer['area'] if farmer else 'Unknown Area',
                    'pincode': farmer['pincode'] if farmer else 'N/A'
                } if farmer else {
                    'name': f'Farmer {r["farmer_id"]}',
                    'mobile_no': 'N/A',
                    'area': 'Unknown Area',
                    'pincode': 'N/A'
                },
                'farmer_name': farmer['name'] if farmer else f'Farmer {r["farmer_id"]}',
                'farmer_phone': farmer['mobile_no'] if farmer else 'N/A',
                'district': farmer['area'] if farmer else 'Unknown Area',
                'crop_name': items_data[0]['animal_type'] if items_data else 'N/A',
                'doctor': {
                    'name': doctor['doctor_name'] if doctor else f'Doctor {r["doctor_id"]}',
                    'hospital': doctor['hospital_name'] if doctor else 'Unknown Hospital',
                    'mobile_no': doctor['mobile_no'] if doctor else 'N/A',
                    'address': doctor['address'] if doctor else 'N/A'
                } if doctor else {
                    'name': f'Doctor {r["doctor_id"]}',
                    'hospital': 'Unknown Hospital',
                    'mobile_no': 'N/A',
                    'address': 'N/A'
                },
                'medicines': [{'medicine_name': m} for m in medicines_list],
                'items': items_data,
                'diagnosis': f'Medical consultation by Dr. {doctor["doctor_name"] if doctor else "Unknown"}'
            }
            recommendations_data.append(rec_data)
        
        # Calculate pagination details
        total_pages = (total + per_page - 1) // per_page
        has_prev = page > 1
        has_next = page < total_pages
        
        return jsonify({
            'recommendations': recommendations_data,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': total_pages,
                'has_prev': has_prev,
                'has_next': has_next
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to fetch claimed recommendations: {str(e)}'}), 500

@app.route('/recommendations/<int:recommendation_id>', methods=['GET'])
@login_required
def get_recommendation_details(recommendation_id):
    try:
        recommendation = get_recommendation_by_id(recommendation_id)
        
        if not recommendation:
            return jsonify({'error': 'Recommendation not found'}), 404
        
        # Get real farmer and doctor data
        farmer = get_farmer_by_id(recommendation['farmer_id'])
        doctor = get_doctor_by_id(recommendation['doctor_id'])
        
        # Get claimed shop data if recommendation is claimed
        claimed_shop = None
        if recommendation['is_claimed'] and recommendation['claimed_by_shop_id']:
            claimed_shop = get_medical_shop_by_id(recommendation['claimed_by_shop_id'])
        
        # Get real recommendation items from database
        recommendation_items = get_recommendation_items_by_recommendation_id(recommendation['id'])
        
        # Convert items to API format
        items_data = []
        medicines_data = []
        for item in recommendation_items:
            if item['antibiotic_name'] and item['antibiotic_name'] != 'Placeholder - Update Required':
                # Calculate total daily dosage
                single_dose = item['single_dose_ml'] or 0
                daily_freq = item['daily_frequency'] or 1
                total_daily_dosage = single_dose * daily_freq
                
                item_data = {
                    'antibiotic_name': item['antibiotic_name'],
                    'disease': item['disease'] or 'Not specified',
                    'animal_type': item['animal_type'] or 'Not specified',
                    'weight': item['weight'] or 0,
                    'age': item['age'] or 0,
                    'single_dose_ml': single_dose,
                    'daily_frequency': daily_freq,
                    'treatment_days': item['treatment_days'] or 1,
                    'total_treatment_dosage_ml': item['total_treatment_dosage_ml'] or 0,
                    'total_daily_dosage_ml': total_daily_dosage
                }
                items_data.append(item_data)
                
                # Create medicine data with dosage info
                medicine_data = {
                    'name': item['antibiotic_name'],
                    'dosage': f'{item["single_dose_ml"]}ml {item["daily_frequency"]} times daily' if item['single_dose_ml'] and item['daily_frequency'] else 'Dosage to be determined',
                    'duration': f'{item["treatment_days"]} days' if item['treatment_days'] else 'Duration to be determined'
                }
                medicines_data.append(medicine_data)
        
        return jsonify({
            'recommendation': {
                'id': recommendation['id'],
                'farmer_id': recommendation['farmer_id'],
                'doctor_id': recommendation['doctor_id'],
                'is_claimed': recommendation['is_claimed'],
                'claimed_by_shop_id': recommendation['claimed_by_shop_id'],
                'claimed_at': recommendation['claimed_at'].isoformat() if recommendation['claimed_at'] else None,
                'claim_notes': recommendation['claim_notes'],
                'claimed_by_shop': {
                    'id': claimed_shop['id'] if claimed_shop else None,
                    'shop_name': claimed_shop['shop_name'] if claimed_shop else None,
                    'owner_name': claimed_shop['owner_name'] if claimed_shop else None,
                    'mobile_no': claimed_shop['mobile_no'] if claimed_shop else None,
                    'address': claimed_shop['address'] if claimed_shop else None,
                    'pincode': claimed_shop['pincode'] if claimed_shop else None
                } if claimed_shop else None,
                'farmer': {
                    'name': farmer['name'] if farmer else f'Farmer {recommendation["farmer_id"]}',
                    'mobile_no': farmer['mobile_no'] if farmer else 'N/A',
                    'area': farmer['area'] if farmer else 'Unknown Area',
                    'address': farmer['area'] if farmer else f'Plot {recommendation["farmer_id"]}, Agricultural Village',
                    'pincode': farmer['pincode'] if farmer else 'N/A'
                } if farmer else {
                    'name': f'Farmer {recommendation["farmer_id"]}',
                    'mobile_no': 'N/A',
                    'area': 'Unknown Area',
                    'address': f'Plot {recommendation["farmer_id"]}, Agricultural Village',
                    'pincode': 'N/A'
                },
                'doctor': {
                    'name': doctor['doctor_name'] if doctor else f'Doctor {recommendation["doctor_id"]}',
                    'hospital': doctor['hospital_name'] if doctor else 'Unknown Hospital',
                    'mobile_no': doctor['mobile_no'] if doctor else 'N/A',
                    'address': doctor['address'] if doctor else 'N/A',
                    'map_link': doctor['map_link'] if doctor else None
                } if doctor else {
                    'name': f'Doctor {recommendation["doctor_id"]}',
                    'hospital': 'Unknown Hospital',
                    'mobile_no': 'N/A',
                    'address': 'N/A',
                    'map_link': None
                },
                'medicines': medicines_data,
                'items': items_data,
                'diagnosis': f'Medical consultation by Dr. {doctor["doctor_name"] if doctor else "Unknown"}',
                'notes': f'Patient: {farmer["name"] if farmer else "Unknown"} from {farmer["area"] if farmer else "Unknown Area"}. Contact: {farmer["mobile_no"] if farmer else "N/A"}'
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to fetch recommendation: {str(e)}'}), 500

@app.route('/recommendations/<int:recommendation_id>/claim', methods=['POST'])
def claim_recommendation_route(recommendation_id):
    try:
        # Check if shop is logged in
        shop_id = session.get('shop_id')
        if not shop_id:
            return jsonify({'error': 'Shop not logged in'}), 401
        
        # Get the recommendation
        recommendation = get_recommendation_by_id(recommendation_id)
        if not recommendation:
            return jsonify({'error': 'Recommendation not found'}), 404
        
        # Check if already claimed
        if recommendation['is_claimed']:
            return jsonify({'error': 'Recommendation already claimed'}), 400
        
        # Get start_date and notes from request
        data = request.get_json() or {}
        start_date_str = data.get('start_date')
        notes = data.get('notes', '')
        
        # Validate start_date is provided
        if not start_date_str:
            return jsonify({'error': 'Start date is required'}), 400
        
        # Parse start_date
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        # Get recommendation items to calculate end date
        recommendation_items = get_recommendation_items_by_recommendation_id(recommendation_id)
        
        if not recommendation_items:
            return jsonify({'error': 'No recommendation items found'}), 404
        
        # Calculate end date based on treatment_days (use maximum if multiple items)
        max_treatment_days = max(item['treatment_days'] for item in recommendation_items if item['treatment_days'])
        end_date = start_date + timedelta(days=max_treatment_days - 1)  # -1 because start day counts as day 1
        
        # Claim the recommendation using db.py function (correct parameters)
        claim_success = claim_recommendation(recommendation_id, shop_id, notes)
        
        if not claim_success:
            return jsonify({'error': 'Failed to claim recommendation'}), 500
        
        # Update recommendation items with dates
        for item in recommendation_items:
            item_end_date = start_date + timedelta(days=item['treatment_days'] - 1)
            update_recommendation_item_dates(item['id'], start_date, item_end_date)
        
        # Send WhatsApp message to farmer after successful claim
        whatsapp_success = False
        whatsapp_message = ""
        
        try:
            app.logger.info(f"DEBUG: Preparing WhatsApp message for recommendation {recommendation_id}")
            app.logger.info(f"DEBUG: Date types before WhatsApp call - start_date: {type(start_date)} = {start_date}, end_date: {type(end_date)} = {end_date}")
            
            # Get farmer details for WhatsApp
            farmer = get_farmer_by_id(recommendation['farmer_id'])
            if farmer and farmer['mobile_no']:
                app.logger.info(f"DEBUG: Farmer found - name: {farmer['name']}, mobile: {farmer['mobile_no']}")
                
                # Send WhatsApp notification with timeout protection
                try:
                    success, message = send_whatsapp_message(
                        farmer_mobile=farmer['mobile_no'],
                        farmer_name=farmer['name'],
                        recommendation_items=recommendation_items,
                        start_date=start_date,
                        end_date=end_date
                    )
                    whatsapp_success = success
                    whatsapp_message = message
                    app.logger.info(f"DEBUG: WhatsApp call completed - success: {success}, message: {message}")
                    
                except Exception as whatsapp_error:
                    # Don't let WhatsApp errors break the main claim process
                    app.logger.error(f"WhatsApp messaging failed but continuing with claim: {str(whatsapp_error)}")
                    whatsapp_success = False
                    whatsapp_message = f"WhatsApp failed: {str(whatsapp_error)}"
                    
            else:
                whatsapp_message = "Farmer mobile number not available"
                app.logger.warning(f"DEBUG: Farmer not found or no mobile number - farmer_id: {recommendation['farmer_id']}")
                
        except Exception as e:
            # Don't let any WhatsApp-related errors break the main claim process
            app.logger.error(f"Error in WhatsApp preparation: {str(e)}")
            whatsapp_success = False
            whatsapp_message = f"WhatsApp preparation error: {str(e)}"
        
        # Get updated recommendation data
        updated_recommendation = get_recommendation_by_id(recommendation_id)
        
        return jsonify({
            'message': 'Recommendation claimed successfully',
            'recommendation_id': recommendation_id,
            'shop_id': shop_id,
            'claimed_at': updated_recommendation['claimed_at'].isoformat() if updated_recommendation['claimed_at'] else datetime.now().isoformat(),
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'max_treatment_days': max_treatment_days,
            'notes': notes,
            'whatsapp_sent': whatsapp_success,
            'whatsapp_message': whatsapp_message
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to claim recommendation: {str(e)}'}), 500

@app.route('/recommendations/search', methods=['GET'])
@login_required
def search_recommendations():
    try:
        # Use db.py function to search unclaimed recommendations
        recommendations_result = search_unclaimed_recommendations()
        recommendations = recommendations_result['recommendations']
        
        # Get real farmer/doctor data for search results
        recommendations_data = []
        for r in recommendations:
            # Get real farmer and doctor data using db.py functions
            farmer = get_farmer_by_id(r['farmer_id'])
            doctor = get_doctor_by_id(r['doctor_id'])
            
            # Get real recommendation items from database using db.py function
            recommendation_items = get_recommendation_items_by_recommendation_id(r['id'])
            
            # Convert items to API format
            items_data = []
            medicines_data = []
            for item in recommendation_items:
                if item['antibiotic_name'] and item['antibiotic_name'] != 'Placeholder - Update Required':
                    # Calculate total daily dosage
                    single_dose = item['single_dose_ml'] or 0
                    daily_freq = item['daily_frequency'] or 1
                    total_daily_dosage = single_dose * daily_freq
                    
                    item_data = {
                        'antibiotic_name': item['antibiotic_name'],
                        'disease': item['disease'] or 'Not specified',
                        'animal_type': item['animal_type'] or 'Not specified',
                        'weight': item['weight'] or 0,
                        'age': item['age'] or 0,
                        'single_dose_ml': single_dose,
                        'daily_frequency': daily_freq,
                        'treatment_days': item['treatment_days'] or 1,
                        'total_treatment_dosage_ml': item['total_treatment_dosage_ml'] or 0,
                        'total_daily_dosage_ml': total_daily_dosage
                    }
                    items_data.append(item_data)
                    medicines_data.append(item['antibiotic_name'])

            rec_data = {
                'id': r['id'],
                'farmer_id': r['farmer_id'],
                'doctor_id': r['doctor_id'],
                'is_claimed': r['is_claimed'],
                'farmer': {
                    'name': farmer['name'] if farmer else f'Farmer {r["farmer_id"]}',
                    'mobile_no': farmer['mobile_no'] if farmer else 'N/A',
                    'area': farmer['area'] if farmer else 'Unknown Area',
                    'pincode': farmer['pincode'] if farmer else 'N/A'
                } if farmer else {
                    'name': f'Farmer {r["farmer_id"]}',
                    'mobile_no': 'N/A',
                    'area': 'Unknown Area',
                    'pincode': 'N/A'
                },
                'doctor': {
                    'name': doctor['doctor_name'] if doctor else f'Doctor {r["doctor_id"]}',
                    'hospital': doctor['hospital_name'] if doctor else 'Unknown Hospital'
                } if doctor else {
                    'name': f'Doctor {r["doctor_id"]}',
                    'hospital': 'Unknown Hospital'
                },
                'medicines': medicines_data,
                'items': items_data,
                'diagnosis': f'Medical consultation by Dr. {doctor["doctor_name"] if doctor else "Unknown"}'
            }
            recommendations_data.append(rec_data)
            
        return jsonify({
            'recommendations': recommendations_data,
            'total': len(recommendations)
        }), 200
    except Exception as e:
        return jsonify({'error': f'Search failed: {str(e)}'}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
