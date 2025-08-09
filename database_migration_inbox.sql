-- Database migration for Inbox functionality
-- Add new Contact table and update MessageHistory table

-- Create Contact table
CREATE TABLE IF NOT EXISTS contact (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    phone_number VARCHAR(32) NOT NULL,
    name VARCHAR(100),
    email VARCHAR(150),
    last_message_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user (id)
);

-- Add new columns to MessageHistory table
ALTER TABLE message_history ADD COLUMN recipient_name VARCHAR(100);
ALTER TABLE message_history ADD COLUMN message_content TEXT;
ALTER TABLE message_history ADD COLUMN message_type VARCHAR(20) DEFAULT 'template';

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_contact_user_phone ON contact(user_id, phone_number);
CREATE INDEX IF NOT EXISTS idx_contact_last_message ON contact(last_message_at DESC);
CREATE INDEX IF NOT EXISTS idx_message_history_recipient ON message_history(user_id, recipient);
CREATE INDEX IF NOT EXISTS idx_message_history_created ON message_history(created_at DESC);

-- Update existing message_history records to have message_type = 'template'
UPDATE message_history SET message_type = 'template' WHERE message_type IS NULL;

-- Create contacts from existing message history (if any)
INSERT OR IGNORE INTO contact (user_id, phone_number, name, last_message_at, created_at)
SELECT 
    user_id,
    recipient as phone_number,
    recipient as name,
    MAX(created_at) as last_message_at,
    MIN(created_at) as created_at
FROM message_history 
GROUP BY user_id, recipient;

-- Update message_content for existing records from template content
UPDATE message_history 
SET message_content = (
    SELECT template.content 
    FROM template 
    WHERE template.id = message_history.template_id
)
WHERE message_content IS NULL AND template_id IS NOT NULL;