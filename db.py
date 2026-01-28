"""
Database operations module using raw SQL queries.
This module handles all database interactions with SQL queries for better control and performance.
"""

import pymysql
import os
import traceback
from datetime import datetime, date
from typing import List, Dict, Optional, Tuple
from dotenv import load_dotenv

load_dotenv()

class DatabaseManager:
    def __init__(self):
        self.host = os.environ.get('DB_HOST', 'localhost')
        self.port = int(os.environ.get('DB_PORT', '3306'))
        self.username = os.environ.get('DB_USERNAME', 'root')
        self.password = os.environ.get('DB_PASSWORD', 'password')
        self.database = os.environ.get('DB_NAME', 'AgriSafe')
        
    def get_connection(self):
        """Get database connection"""
        try:
            connection = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.username,
                password=self.password,
                database=self.database,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            return connection
        except Exception as e:
            print(f"Database connection error: {e}")
            raise

    def execute_query(self, query: str, params: tuple = None) -> List[Dict]:
        """Execute SELECT query and return results"""
        connection = None
        try:
            connection = self.get_connection()
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()
        except Exception as e:
            print(f"Query execution error: {e}")
            print(f"Query: {query}")
            print(f"Params: {params}")
            raise
        finally:
            if connection:
                connection.close()

    def execute_insert_update_delete(self, query: str, params: tuple = None) -> int:
        """Execute INSERT, UPDATE, DELETE query and return affected rows or last insert id"""
        connection = None
        try:
            connection = self.get_connection()
            with connection.cursor() as cursor:
                affected_rows = cursor.execute(query, params)
                connection.commit()
                # Return last insert id for INSERT operations, affected rows for others
                return cursor.lastrowid if 'INSERT' in query.upper() else affected_rows
        except Exception as e:
            if connection:
                connection.rollback()
            print(f"Query execution error: {e}")
            print(f"Query: {query}")
            print(f"Params: {params}")
            raise
        finally:
            if connection:
                connection.close()

# Initialize database manager
db_manager = DatabaseManager()

# ==================== MEDICAL SHOP OPERATIONS ====================

def get_medical_shop_by_mobile(mobile_no: str) -> Optional[Dict]:
    """Get medical shop by mobile number"""
    query = """
        SELECT id, shop_name, owner_name, mobile_no, email, license_number, 
               pincode, address, city, state, password_hash, is_verified, 
               is_active, created_at, updated_at
        FROM medical_shops 
        WHERE mobile_no = %s
    """
    results = db_manager.execute_query(query, (mobile_no,))
    return results[0] if results else None

def get_medical_shop_by_id(shop_id: int) -> Optional[Dict]:
    """Get medical shop by ID"""
    query = """
        SELECT id, shop_name, owner_name, mobile_no, email, license_number, 
               pincode, address, city, state, password_hash, is_verified, 
               is_active, created_at, updated_at
        FROM medical_shops 
        WHERE id = %s
    """
    results = db_manager.execute_query(query, (shop_id,))
    return results[0] if results else None

def create_medical_shop(shop_data: Dict) -> int:
    """Create new medical shop and return shop ID"""
    query = """
        INSERT INTO medical_shops 
        (shop_name, owner_name, mobile_no, email, license_number, pincode, 
         address, city, state, password_hash, is_verified, is_active)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    params = (
        shop_data['shop_name'], shop_data['owner_name'], shop_data['mobile_no'],
        shop_data.get('email'), shop_data['license_number'], shop_data['pincode'],
        shop_data['address'], shop_data['city'], shop_data['state'],
        shop_data['password_hash'], shop_data.get('is_verified', False),
        shop_data.get('is_active', True)
    )
    return db_manager.execute_insert_update_delete(query, params)

def update_medical_shop_profile(shop_id: int, shop_data: Dict) -> bool:
    """Update medical shop profile"""
    try:
        # Build UPDATE query dynamically based on provided data
        update_fields = []
        params = []
        
        # Map form fields to database columns
        field_mapping = {
            'shop_name': 'shop_name',
            'owner_name': 'owner_name', 
            'phone_number': 'mobile_no',
            'email': 'email',
            'license_number': 'license_number',
            'district': 'city',  # Using city field for district
            'address': 'address'
        }
        
        for form_field, db_column in field_mapping.items():
            if form_field in shop_data and shop_data[form_field] is not None:
                update_fields.append(f"{db_column} = %s")
                params.append(shop_data[form_field])
        
        if not update_fields:
            return True  # Nothing to update
            
        # Add updated_at timestamp
        update_fields.append("updated_at = %s")
        params.append(datetime.now())
        
        # Add shop_id for WHERE clause
        params.append(shop_id)
        
        query = f"""
            UPDATE medical_shops 
            SET {', '.join(update_fields)}
            WHERE id = %s
        """
        
        rows_affected = db_manager.execute_insert_update_delete(query, tuple(params))
        return rows_affected > 0
        
    except Exception as e:
        print(f"Error updating shop profile: {e}")
        return False

# ==================== FARMER OPERATIONS ====================

def get_farmer_by_id(farmer_id: int) -> Optional[Dict]:
    """Get farmer by ID"""
    query = """
        SELECT id, name, mobile_no, area, pincode, doctor_id, created_at, updated_at
        FROM farmers 
        WHERE id = %s
    """
    results = db_manager.execute_query(query, (farmer_id,))
    return results[0] if results else None

def create_farmer(farmer_data: Dict) -> int:
    """Create new farmer and return farmer ID"""
    query = """
        INSERT INTO farmers (name, mobile_no, area, pincode, doctor_id)
        VALUES (%s, %s, %s, %s, %s)
    """
    params = (
        farmer_data['name'], farmer_data['mobile_no'], 
        farmer_data.get('area'), farmer_data.get('pincode'),
        farmer_data['doctor_id']
    )
    return db_manager.execute_insert_update_delete(query, params)

# ==================== DOCTOR OPERATIONS ====================

def get_doctor_by_id(doctor_id: int) -> Optional[Dict]:
    """Get doctor by ID"""
    query = """
        SELECT id, hospital_name, doctor_name, mobile_no, pincode, address, 
               map_link, password_hash, created_at
        FROM doctors 
        WHERE id = %s
    """
    results = db_manager.execute_query(query, (doctor_id,))
    return results[0] if results else None

def create_doctor(doctor_data: Dict) -> int:
    """Create new doctor and return doctor ID"""
    query = """
        INSERT INTO doctors 
        (hospital_name, doctor_name, mobile_no, pincode, address, map_link, password_hash)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    params = (
        doctor_data['hospital_name'], doctor_data['doctor_name'],
        doctor_data['mobile_no'], doctor_data.get('pincode'),
        doctor_data.get('address'), doctor_data.get('map_link'),
        doctor_data.get('password_hash')
    )
    return db_manager.execute_insert_update_delete(query, params)

# ==================== RECOMMENDATION OPERATIONS ====================

def get_recommendation_by_id(recommendation_id: int) -> Optional[Dict]:
    """Get recommendation by ID"""
    query = """
        SELECT id, farmer_id, doctor_id, is_claimed, claimed_by_shop_id, 
               claimed_at, claim_notes, created_at, updated_at
        FROM medicine_recommendations 
        WHERE id = %s
    """
    results = db_manager.execute_query(query, (recommendation_id,))
    return results[0] if results else None

def get_recommendations_by_shop_id(shop_id: int, page: int = 1, per_page: int = 10, 
                                 from_date: str = None, to_date: str = None, 
                                 animal_type: str = None) -> Tuple[List[Dict], int]:
    """Get claimed recommendations by shop ID with pagination and filters"""
    
    # Base query
    base_query = """
        FROM medicine_recommendations mr
        WHERE mr.claimed_by_shop_id = %s AND mr.is_claimed = 1
    """
    params = [shop_id]
    
    # Add date filters
    if from_date:
        base_query += " AND mr.claimed_at >= %s"
        params.append(from_date)
    
    if to_date:
        base_query += " AND mr.claimed_at < %s"
        params.append(to_date)
    
    # Add animal type filter
    if animal_type:
        base_query += """ AND EXISTS (
            SELECT 1 FROM recommendation_items ri 
            WHERE ri.recommendation_id = mr.id AND ri.animal_type = %s
        )"""
        params.append(animal_type)
    
    # Get total count
    count_query = f"SELECT COUNT(*) as total {base_query}"
    total_results = db_manager.execute_query(count_query, tuple(params))
    total = total_results[0]['total'] if total_results else 0
    
    # Get paginated results
    offset = (page - 1) * per_page
    data_query = f"""
        SELECT mr.id, mr.farmer_id, mr.doctor_id, mr.is_claimed, 
               mr.claimed_by_shop_id, mr.claimed_at, mr.claim_notes, 
               mr.created_at, mr.updated_at
        {base_query}
        ORDER BY mr.claimed_at DESC
        LIMIT %s OFFSET %s
    """
    params.extend([per_page, offset])
    
    recommendations = db_manager.execute_query(data_query, tuple(params))
    return recommendations, total

def claim_recommendation(recommendation_id: int, shop_id: int, claim_notes: str = None) -> bool:
    """Claim a recommendation"""
    query = """
        UPDATE medicine_recommendations 
        SET is_claimed = 1, claimed_by_shop_id = %s, claimed_at = %s, claim_notes = %s, updated_at = %s
        WHERE id = %s AND is_claimed = 0
    """
    now = datetime.now()
    params = (shop_id, now, claim_notes, now, recommendation_id)
    affected_rows = db_manager.execute_insert_update_delete(query, params)
    return affected_rows > 0

def create_recommendation(farmer_id: int, doctor_id: int) -> int:
    """Create new recommendation and return recommendation ID"""
    query = """
        INSERT INTO medicine_recommendations (farmer_id, doctor_id, is_claimed)
        VALUES (%s, %s, 0)
    """
    return db_manager.execute_insert_update_delete(query, (farmer_id, doctor_id))

# ==================== RECOMMENDATION ITEMS OPERATIONS ====================

def get_recommendation_items_by_recommendation_id(recommendation_id: int) -> List[Dict]:
    """Get all recommendation items for a recommendation"""
    query = """
        SELECT id, recommendation_id, antibiotic_name, total_limit, animal_type,
               weight, age, disease, single_dose_ml, start_date, end_date,
               treatment_days, daily_frequency, total_daily_dosage_ml,
               total_treatment_dosage_ml, frequency_description, dosage_per_kg,
               age_category, confidence, calculation_note, created_at, updated_at
        FROM recommendation_items 
        WHERE recommendation_id = %s
        ORDER BY id
    """
    return db_manager.execute_query(query, (recommendation_id,))

def create_recommendation_item(item_data: Dict) -> int:
    """Create new recommendation item and return item ID"""
    query = """
        INSERT INTO recommendation_items 
        (recommendation_id, antibiotic_name, total_limit, animal_type, weight, age,
         disease, single_dose_ml, start_date, end_date, treatment_days, daily_frequency,
         total_daily_dosage_ml, total_treatment_dosage_ml, frequency_description,
         dosage_per_kg, age_category, confidence, calculation_note)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    params = (
        item_data['recommendation_id'], item_data.get('antibiotic_name'),
        item_data.get('total_limit'), item_data.get('animal_type'),
        item_data.get('weight'), item_data.get('age'),
        item_data.get('disease'), item_data.get('single_dose_ml'),
        item_data.get('start_date'), item_data.get('end_date'),
        item_data.get('treatment_days'), item_data.get('daily_frequency'),
        item_data.get('total_daily_dosage_ml'), item_data.get('total_treatment_dosage_ml'),
        item_data.get('frequency_description'), item_data.get('dosage_per_kg'),
        item_data.get('age_category'), item_data.get('confidence'),
        item_data.get('calculation_note')
    )
    return db_manager.execute_insert_update_delete(query, params)

def update_recommendation_item_dates(item_id: int, start_date: date, end_date: date) -> bool:
    """Update start and end dates for recommendation item"""
    query = """
        UPDATE recommendation_items 
        SET start_date = %s, end_date = %s, updated_at = %s
        WHERE id = %s
    """
    params = (start_date, end_date, datetime.now(), item_id)
    affected_rows = db_manager.execute_insert_update_delete(query, params)
    return affected_rows > 0

# ==================== STATISTICS OPERATIONS ====================

def get_shop_statistics(shop_id: int) -> Dict:
    """Get shop statistics (total, today's, week's, month's claims)"""
    
    # Total claims
    total_query = """
        SELECT COUNT(*) as count FROM medicine_recommendations 
        WHERE claimed_by_shop_id = %s AND is_claimed = 1
    """
    total_result = db_manager.execute_query(total_query, (shop_id,))
    total_claims = total_result[0]['count'] if total_result else 0
    
    # Today's claims
    today_query = """
        SELECT COUNT(*) as count FROM medicine_recommendations 
        WHERE claimed_by_shop_id = %s AND is_claimed = 1 
        AND DATE(claimed_at) = CURDATE()
    """
    today_result = db_manager.execute_query(today_query, (shop_id,))
    todays_claims = today_result[0]['count'] if today_result else 0
    
    # This week's claims (Monday to Sunday)
    week_query = """
        SELECT COUNT(*) as count FROM medicine_recommendations 
        WHERE claimed_by_shop_id = %s AND is_claimed = 1 
        AND YEARWEEK(claimed_at, 1) = YEARWEEK(CURDATE(), 1)
    """
    week_result = db_manager.execute_query(week_query, (shop_id,))
    this_week_claims = week_result[0]['count'] if week_result else 0
    
    # This month's claims
    month_query = """
        SELECT COUNT(*) as count FROM medicine_recommendations 
        WHERE claimed_by_shop_id = %s AND is_claimed = 1 
        AND YEAR(claimed_at) = YEAR(CURDATE()) 
        AND MONTH(claimed_at) = MONTH(CURDATE())
    """
    month_result = db_manager.execute_query(month_query, (shop_id,))
    this_month_claims = month_result[0]['count'] if month_result else 0
    
    return {
        'total_claims': total_claims,
        'todays_claims': todays_claims,
        'this_week_claims': this_week_claims,
        'this_month_claims': this_month_claims
    }

# ==================== SEARCH OPERATIONS ====================

def search_unclaimed_recommendations(search_query: str = None, pincode: str = None, 
                                   animal_type: str = None, page: int = 1, 
                                   per_page: int = 10) -> Tuple[List[Dict], int]:
    """Search for unclaimed recommendations with filters"""
    
    base_query = """
        FROM medicine_recommendations mr
        LEFT JOIN farmers f ON mr.farmer_id = f.id
        LEFT JOIN doctors d ON mr.doctor_id = d.id
        WHERE mr.is_claimed = 0
    """
    params = []
    
    # Add search filters
    if search_query:
        try:
            # If search_query is numeric, search by recommendation ID
            rec_id = int(search_query)
            base_query += " AND mr.id = %s"
            params.append(rec_id)
        except ValueError:
            # If not numeric, search by farmer name or area
            base_query += " AND (f.name LIKE %s OR f.area LIKE %s)"
            search_pattern = f"%{search_query}%"
            params.extend([search_pattern, search_pattern])
    
    if pincode:
        base_query += " AND (f.pincode = %s OR d.pincode = %s)"
        params.extend([pincode, pincode])
    
    if animal_type:
        base_query += """ AND EXISTS (
            SELECT 1 FROM recommendation_items ri 
            WHERE ri.recommendation_id = mr.id AND ri.animal_type = %s
        )"""
        params.append(animal_type)
    
    # Get total count
    count_query = f"SELECT COUNT(*) as total {base_query}"
    total_results = db_manager.execute_query(count_query, tuple(params))
    total = total_results[0]['total'] if total_results else 0
    
    # Get paginated results
    offset = (page - 1) * per_page
    data_query = f"""
        SELECT mr.id, mr.farmer_id, mr.doctor_id, mr.created_at,
               f.name as farmer_name, f.mobile_no as farmer_mobile, 
               f.area as farmer_area, f.pincode as farmer_pincode,
               d.doctor_name, d.hospital_name, d.mobile_no as doctor_mobile,
               d.address as doctor_address, d.pincode as doctor_pincode
        {base_query}
        ORDER BY mr.created_at DESC
        LIMIT %s OFFSET %s
    """
    params.extend([per_page, offset])
    
    recommendations = db_manager.execute_query(data_query, tuple(params))
    return recommendations, total

# ==================== TEST FUNCTION ====================

def test_database_connection() -> bool:
    """Test database connection and basic operations"""
    try:
        # Test connection
        connection = db_manager.get_connection()
        connection.close()
        
        # Test basic query
        result = db_manager.execute_query("SELECT 1 as test")
        
        print("✅ Database connection successful!")
        print("✅ Basic query execution successful!")
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    """Test database operations when run directly"""
    print("Testing database operations...")
    test_database_connection()