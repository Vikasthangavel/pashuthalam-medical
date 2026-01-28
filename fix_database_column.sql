-- ===================================================================
-- Fix Database Column Name Issue
-- ===================================================================
-- This script will rename the column from 'shop_owner' to 'owner_name'
-- in the medical_shops table to match the application code
-- ===================================================================

USE AgriSafe;

-- Check if the column 'shop_owner' exists and rename it to 'owner_name'
-- Note: Run this only if you have 'shop_owner' column instead of 'owner_name'

-- Method 1: Using ALTER TABLE CHANGE (MySQL/MariaDB)
ALTER TABLE medical_shops 
CHANGE COLUMN shop_owner owner_name VARCHAR(100) NOT NULL;

-- Alternative Method 2: If the above doesn't work, use RENAME COLUMN (MySQL 8.0+)
-- ALTER TABLE medical_shops 
-- RENAME COLUMN shop_owner TO owner_name;

-- Verify the column structure
DESCRIBE medical_shops;