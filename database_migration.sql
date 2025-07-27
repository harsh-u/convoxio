-- Database Migration: Add UTILITY category to template table
-- Run this SQL command in your MySQL database

-- Method 1: Alter the enum directly (MySQL 8.0+)
ALTER TABLE template 
MODIFY COLUMN category ENUM('TRANSACTIONAL', 'MARKETING', 'OTP', 'UTILITY') DEFAULT 'TRANSACTIONAL';

-- Method 2: If the above doesn't work, you can recreate the column
-- ALTER TABLE template DROP COLUMN category;
-- ALTER TABLE template ADD COLUMN category ENUM('TRANSACTIONAL', 'MARKETING', 'OTP', 'UTILITY') DEFAULT 'TRANSACTIONAL';

-- Verify the change
DESCRIBE template; 