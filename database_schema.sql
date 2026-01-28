-- ===================================================================
-- Medical Shop Management System - Database Schema
-- ===================================================================
-- This file contains the complete database schema for the medical shop
-- management system with WhatsApp integration.
-- 
-- Usage: 
--   mysql -u username -p database_name < database_schema.sql
-- ===================================================================

-- Create database if it doesn't exist
CREATE DATABASE IF NOT EXISTS AgriSafe CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE AgriSafe;

-- ===================================================================
-- Table: medical_shops
-- Purpose: Store medical shop information and credentials
-- ===================================================================
CREATE TABLE IF NOT EXISTS medical_shops (
    id INT PRIMARY KEY AUTO_INCREMENT,
    shop_name VARCHAR(100) NOT NULL,
    owner_name VARCHAR(100) NOT NULL,
    mobile_no VARCHAR(15) NOT NULL UNIQUE,
    email VARCHAR(100),
    license_number VARCHAR(50) NOT NULL,
    pincode VARCHAR(10) NOT NULL,
    address TEXT NOT NULL,
    city VARCHAR(50) NOT NULL,
    state VARCHAR(50) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_mobile_no (mobile_no),
    INDEX idx_pincode (pincode),
    INDEX idx_license (license_number),
    INDEX idx_is_verified (is_verified),
    INDEX idx_is_active (is_active)
);

-- ===================================================================
-- Table: doctors
-- Purpose: Store doctor/veterinarian information
-- ===================================================================
CREATE TABLE IF NOT EXISTS doctors (
    id INT PRIMARY KEY AUTO_INCREMENT,
    hospital_name VARCHAR(255) NOT NULL,
    doctor_name VARCHAR(255) NOT NULL,
    mobile_no VARCHAR(20) NOT NULL,
    pincode VARCHAR(10),
    address TEXT,
    map_link TEXT,
    password_hash VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_doctor_mobile (mobile_no),
    INDEX idx_doctor_pincode (pincode),
    INDEX idx_doctor_name (doctor_name)
);

-- ===================================================================
-- Table: farmers
-- Purpose: Store farmer information
-- ===================================================================
CREATE TABLE IF NOT EXISTS farmers (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    mobile_no VARCHAR(20) NOT NULL,
    area TEXT,
    pincode VARCHAR(10),
    doctor_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_farmer_mobile (mobile_no),
    INDEX idx_farmer_pincode (pincode),
    INDEX idx_farmer_doctor (doctor_id),
    INDEX idx_farmer_name (name)
);

-- ===================================================================
-- Table: medicine_recommendations
-- Purpose: Store medicine recommendation records
-- ===================================================================
CREATE TABLE IF NOT EXISTS medicine_recommendations (
    id INT PRIMARY KEY AUTO_INCREMENT,
    farmer_id INT NOT NULL,
    doctor_id INT NOT NULL,
    is_claimed BOOLEAN NOT NULL DEFAULT FALSE,
    claimed_by_shop_id INT,
    claimed_at TIMESTAMP NULL,
    claim_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (farmer_id) REFERENCES farmers(id) ON DELETE CASCADE,
    FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE CASCADE,
    FOREIGN KEY (claimed_by_shop_id) REFERENCES medical_shops(id) ON DELETE SET NULL,
    
    INDEX idx_recommendation_farmer (farmer_id),
    INDEX idx_recommendation_doctor (doctor_id),
    INDEX idx_recommendation_claimed (is_claimed),
    INDEX idx_recommendation_shop (claimed_by_shop_id),
    INDEX idx_recommendation_created (created_at)
);

-- ===================================================================
-- Table: recommendation_items
-- Purpose: Store individual antibiotic/medicine items within recommendations
-- ===================================================================
CREATE TABLE IF NOT EXISTS recommendation_items (
    id INT PRIMARY KEY AUTO_INCREMENT,
    recommendation_id INT NOT NULL,
    antibiotic_name VARCHAR(100),
    total_limit DECIMAL(10,2),
    animal_type VARCHAR(50),
    weight DECIMAL(8,2),
    age INT,
    disease VARCHAR(100),
    single_dose_ml DECIMAL(10,2),
    start_date DATE,
    end_date DATE,
    treatment_days INT,
    daily_frequency INT,
    total_daily_dosage_ml DECIMAL(10,2),
    total_treatment_dosage_ml DECIMAL(10,2),
    frequency_description VARCHAR(100),
    dosage_per_kg DECIMAL(10,2),
    age_category VARCHAR(50),
    confidence DECIMAL(5,2),
    calculation_note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (recommendation_id) REFERENCES medicine_recommendations(id) ON DELETE CASCADE,
    
    INDEX idx_item_recommendation (recommendation_id),
    INDEX idx_item_antibiotic (antibiotic_name),
    INDEX idx_item_animal_type (animal_type),
    INDEX idx_item_disease (disease),
    INDEX idx_item_dates (start_date, end_date)
);

-- ===================================================================
-- Insert Sample Data (Optional)
-- ===================================================================

-- Sample Doctor
INSERT IGNORE INTO doctors (id, hospital_name, doctor_name, mobile_no, pincode, address) VALUES
(1, 'Veterinary Care Center', 'Dr. Rajesh Kumar', '9876543210', '560001', 'Bangalore, Karnataka');

-- Sample Farmers
INSERT IGNORE INTO farmers (id, name, mobile_no, area, pincode, doctor_id) VALUES
(1, 'VIKAS T', '6381459911', 'Rural Area, Tamil Nadu', '600001', 1),
(2, 'Ramesh Patel', '9876543211', 'Gujarat Farm Belt', '380001', 1),
(3, 'Kamalesh Singh', '918122762374', 'Punjab Agricultural Zone', '140001', 1);

-- ===================================================================
-- Database Optimization
-- ===================================================================

-- Analyze tables for optimization
ANALYZE TABLE medical_shops, doctors, farmers, medicine_recommendations, recommendation_items;

-- ===================================================================
-- Permissions (Uncomment and modify as needed)
-- ===================================================================

-- Create application user (modify credentials as needed)
-- CREATE USER IF NOT EXISTS 'agrisafe_user'@'localhost' IDENTIFIED BY 'secure_password';
-- GRANT SELECT, INSERT, UPDATE, DELETE ON AgriSafe.* TO 'agrisafe_user'@'localhost';
-- FLUSH PRIVILEGES;

-- ===================================================================
-- Schema Information
-- ===================================================================

SELECT 
    'Database Schema Created Successfully' as Status,
    COUNT(*) as Tables_Created
FROM information_schema.tables 
WHERE table_schema = 'AgriSafe';

-- Show all created tables
SELECT 
    TABLE_NAME as 'Table Name',
    TABLE_ROWS as 'Estimated Rows',
    ROUND((DATA_LENGTH + INDEX_LENGTH) / 1024 / 1024, 2) as 'Size (MB)'
FROM information_schema.tables 
WHERE table_schema = 'AgriSafe'
ORDER BY TABLE_NAME;