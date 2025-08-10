-- Fix MySQL migration - Run these commands one by one

-- 1. Create Contact table (corrected MySQL syntax)
CREATE TABLE contact (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    phone_number VARCHAR(32) NOT NULL,
    name VARCHAR(100),
    email VARCHAR(150),
    last_message_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user (id)
);

-- 2. Create indexes for better performance
CREATE INDEX idx_contact_user_phone ON contact(user_id, phone_number);
CREATE INDEX idx_contact_last_message ON contact(last_message_at DESC);
CREATE INDEX idx_message_history_recipient ON message_history(user_id, recipient);
CREATE INDEX idx_message_history_created ON message_history(created_at DESC);

-- 3. Create contacts from existing message history
INSERT IGNORE INTO contact (user_id, phone_number, name, last_message_at, created_at)
SELECT 
    user_id,
    recipient as phone_number,
    recipient as name,
    MAX(created_at) as last_message_at,
    MIN(created_at) as created_at
FROM message_history 
GROUP BY user_id, recipient;