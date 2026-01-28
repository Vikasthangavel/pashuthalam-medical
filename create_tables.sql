-- ===================================================================
-- Medical Shop Management System - Simple Database Schema
-- ===================================================================
-- Compatible with MySQL/MariaDB
-- Run this file to create all required tables
-- ===================================================================

-- Use your database (modify as needed)
CREATE DATABASE AgriSafe;
USE AgriSafe;

-- ===================================================================
-- Table: medical_shops
-- ===================================================================
CREATE TABLE medical_shops (
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
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- ===================================================================
-- Table: doctors
-- ===================================================================
CREATE TABLE doctors (
    id INT PRIMARY KEY AUTO_INCREMENT,
    hospital_name VARCHAR(255) NOT NULL,
    doctor_name VARCHAR(255) NOT NULL,
    mobile_no VARCHAR(20) NOT NULL,
    pincode VARCHAR(10),
    address TEXT,
    map_link TEXT,
    password_hash VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===================================================================
-- Table: farmers
-- ===================================================================
CREATE TABLE farmers (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    mobile_no VARCHAR(20) NOT NULL,
    area TEXT,
    pincode VARCHAR(10),
    doctor_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- ===================================================================
-- Table: medicine_recommendations
-- ===================================================================
CREATE TABLE medicine_recommendations (
    id INT PRIMARY KEY AUTO_INCREMENT,
    farmer_id INT NOT NULL,
    doctor_id INT NOT NULL,
    is_claimed BOOLEAN NOT NULL DEFAULT FALSE,
    claimed_by_shop_id INT,
    claimed_at TIMESTAMP NULL,
    claim_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (farmer_id) REFERENCES farmers(id),
    FOREIGN KEY (doctor_id) REFERENCES doctors(id),
    FOREIGN KEY (claimed_by_shop_id) REFERENCES medical_shops(id)
);

-- ===================================================================
-- Table: recommendation_items
-- ===================================================================
CREATE TABLE recommendation_items (
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
    
    FOREIGN KEY (recommendation_id) REFERENCES medicine_recommendations(id)
);

-- ===================================================================
-- Create Indexes for Performance
-- ===================================================================
CREATE INDEX idx_medical_shops_mobile ON medical_shops(mobile_no);
CREATE INDEX idx_medical_shops_pincode ON medical_shops(pincode);
CREATE INDEX idx_farmers_mobile ON farmers(mobile_no);
CREATE INDEX idx_recommendations_claimed ON medicine_recommendations(is_claimed);
CREATE INDEX idx_recommendations_farmer ON medicine_recommendations(farmer_id);
CREATE INDEX idx_items_recommendation ON recommendation_items(recommendation_id);

-- ===================================================================
-- Insert Sample Data
-- ===================================================================
INSERT INTO doctors (id, hospital_name, doctor_name, mobile_no, pincode) VALUES
(1, 'Veterinary Care Center', 'Dr. Rajesh Kumar', '9876543210', '560001');

INSERT INTO farmers (id, name, mobile_no, area, pincode, doctor_id) VALUES
(1, 'VIKAS T', '6381459911', 'Tamil Nadu', '600001', 1),
(2, 'Ramesh Patel', '9876543211', 'Gujarat', '380001', 1),
(3, 'Kamalesh Singh', '918122762374', 'Punjab', '140001', 1);