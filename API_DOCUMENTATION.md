# WhatsApp Business API - Mobile App Endpoints

This document outlines all the REST API endpoints available for the mobile application.

## Base URL
```
http://localhost:5001/api
```

## Authentication
All endpoints (except login/register) require authentication. The API uses session-based authentication with cookies.

## Response Format
All responses follow this format:
```json
{
  "success": true/false,
  "message": "Human readable message",
  "data": {...}, // Response data (varies by endpoint)
  "error": "Error message" // Only present when success is false
}
```

---

## Authentication Endpoints

### POST /api/auth/register
Register a new user account.

**Request Body:**
```json
{
  "business_name": "My Business",
  "email": "user@example.com",
  "phone_number": "919876543210",
  "password": "password123"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Registration successful",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "business_name": "My Business",
    "phone_number": "919876543210",
    "onboarding_status": "Pending",
    "message_limit": 1000,
    "messages_sent_this_month": 0
  }
}
```

### POST /api/auth/login
Login with email and password.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Login successful",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "business_name": "My Business",
    "onboarding_status": "Verified",
    "message_limit": 1000,
    "messages_sent_this_month": 45,
    "waba_id": "123456789",
    "phone_number_id": "987654321",
    "is_verified": true
  }
}
```

### POST /api/auth/logout
Logout current user.

**Response:**
```json
{
  "success": true,
  "message": "Logout successful"
}
```

### GET /api/auth/user/status
Get current user status and details.

**Response:**
```json
{
  "success": true,
  "user": {
    "id": 1,
    "email": "user@example.com",
    "business_name": "My Business",
    "onboarding_status": "Verified",
    "message_limit": 1000,
    "messages_sent_this_month": 45,
    "remaining_messages": 955,
    "can_send_message": true,
    "is_premium": false
  }
}
```

---

## Dashboard Endpoints

### GET /api/dashboard
Get complete dashboard data.

**Response:**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": 1,
      "email": "user@example.com",
      "business_name": "My Business",
      "onboarding_status": "Verified",
      "message_limit": 1000,
      "messages_sent_this_month": 45,
      "remaining_messages": 955
    },
    "setup_status": {
      "docs_uploaded": true,
      "has_pan": true,
      "has_gst": true,
      "can_send": true,
      "whatsapp_connected": true
    },
    "stats": {
      "total_messages": 150,
      "messages_today": 5,
      "template_count": 3,
      "approved_templates": 2,
      "contact_count": 25
    },
    "recent_messages": [
      {
        "id": 1,
        "recipient": "919876543210",
        "recipient_name": "John Doe",
        "template_id": 1,
        "message_content": "Hello {{name}}",
        "status": "delivered",
        "created_at": "2024-01-15T10:30:00",
        "template_name": "Welcome Message"
      }
    ]
  }
}
```

### GET /api/quick-stats
Get quick statistics for dashboard widgets.

**Response:**
```json
{
  "success": true,
  "stats": {
    "total_messages": 150,
    "messages_today": 5,
    "messages_this_week": 25,
    "messages_this_month": 45,
    "delivery_rate": 95.5,
    "read_rate": 78.2,
    "remaining_messages": 955,
    "status_breakdown": [
      {"status": "delivered", "count": 120},
      {"status": "read", "count": 98},
      {"status": "failed", "count": 5}
    ]
  }
}
```

---

## Template Management

### GET /api/templates
Get all templates for current user.

**Response:**
```json
{
  "success": true,
  "templates": [
    {
      "id": 1,
      "name": "welcome_message",
      "language": "en_US",
      "content": "Welcome to our service!",
      "status": "Approved",
      "category": "TRANSACTIONAL",
      "header_type": "TEXT",
      "header_text": "Welcome!",
      "footer_text": "Thank you",
      "created_at": "2024-01-15T10:30:00"
    }
  ]
}
```

### GET /api/templates/approved
Get only approved templates for messaging.

### POST /api/templates
Create a new message template.

**Request Body:**
```json
{
  "name": "order_confirmation",
  "language": "en_US",
  "content": "Your order #{{order_id}} has been confirmed!",
  "category": "TRANSACTIONAL",
  "header_type": "TEXT",
  "header_text": "Order Update",
  "footer_text": "Thank you for shopping with us",
  "button1_type": "QUICK_REPLY",
  "button1_text": "Track Order"
}
```

### GET /api/templates/{template_id}
Get specific template details.

### DELETE /api/templates/{template_id}
Delete a template.

---

## Messaging

### POST /api/send-message
Send individual WhatsApp message.

**Request Body:**
```json
{
  "recipient": "919876543210",
  "recipient_name": "John Doe",
  "template_id": 1
}
```

**Response:**
```json
{
  "success": true,
  "message": "Message sent successfully",
  "message_id": 123,
  "meta_message_id": "wamid.xxx",
  "remaining_messages": 954
}
```

### POST /api/send-bulk
Send bulk WhatsApp messages.

**Request Body:**
```json
{
  "template_id": 1,
  "recipients_list": [
    "919876543210",
    "919876543211",
    "919876543212"
  ]
}
```

**Response:**
```json
{
  "success": true,
  "message": "Bulk send completed: 3 sent, 0 failed",
  "sent_count": 3,
  "failed_count": 0,
  "remaining_messages": 952,
  "results": [
    {
      "recipient": "919876543210",
      "status": "sent",
      "message_id": 124
    }
  ]
}
```

### POST /api/schedule-message
Schedule a message for future delivery.

**Request Body:**
```json
{
  "recipient": "919876543210",
  "template_id": 1,
  "scheduled_datetime": "2024-01-16T14:30:00"
}
```

### GET /api/scheduled-messages
Get all scheduled messages.

### POST /api/scheduled-messages/{msg_id}/cancel
Cancel a scheduled message.

### GET /api/message-history
Get message history with pagination.

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Items per page (default: 20)
- `status` (optional): Filter by status

---

## File Uploads

### POST /api/upload
Upload business documents (PAN/GST).

**Request:** Multipart form data with files:
- `pan_file`: PAN document (PDF/JPG/PNG)
- `gst_file`: GST document (PDF/JPG/PNG)

**Response:**
```json
{
  "success": true,
  "message": "2 document(s) uploaded successfully",
  "uploaded_files": [
    {
      "filename": "pan_document.pdf",
      "filetype": "PAN",
      "size": 1024000
    }
  ],
  "docs_complete": true,
  "has_pan": true,
  "has_gst": true
}
```

### GET /api/uploads
Get all uploaded documents.

### DELETE /api/uploads/{upload_id}
Delete an uploaded document.

---

## Analytics

### GET /api/analytics
Get comprehensive analytics data.

**Query Parameters:**
- `days` (optional): Number of days for analysis (default: 30)

**Response:**
```json
{
  "success": true,
  "analytics": {
    "overview": {
      "total_messages": 150,
      "messages_this_period": 45,
      "delivery_rate": 95.5,
      "read_rate": 78.2,
      "remaining_messages": 955,
      "total_contacts": 25,
      "recent_messages": 15
    },
    "daily_stats": [
      {
        "date": "2024-01-15",
        "day": "Mon",
        "count": 5
      }
    ],
    "status_breakdown": [
      {"status": "delivered", "count": 120},
      {"status": "read", "count": 98}
    ],
    "template_performance": [
      {"name": "welcome_message", "usage_count": 50}
    ]
  }
}
```

### GET /api/analytics/summary
Get quick analytics summary.

### GET /api/analytics/templates
Get detailed template performance analytics.

---

## Onboarding

### POST /api/onboard/start
Start WhatsApp Business onboarding OAuth flow.

**Response:**
```json
{
  "success": true,
  "oauth_url": "https://www.facebook.com/v19.0/dialog/oauth?...",
  "message": "Redirect user to this URL to complete WhatsApp setup"
}
```

### POST /api/onboard/simple-setup
Complete simple WhatsApp setup for small businesses.

**Request Body:**
```json
{
  "whatsapp_number": "919876543210",
  "otp": "123456"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Setup complete! You can now send WhatsApp messages to your customers.",
  "user": {
    "id": 1,
    "onboarding_status": "Verified",
    "waba_id": "platform_waba_id_123",
    "phone_number_id": "phone_abc123",
    "phone_number": "919876543210"
  }
}
```

### POST /api/onboard/update-credentials
Manually update WhatsApp credentials (for testing).

**Request Body:**
```json
{
  "access_token": "your_access_token",
  "waba_id": "your_waba_id", 
  "phone_id": "your_phone_number_id"
}
```

### POST /api/onboard/reset
Reset WhatsApp connection for testing.

### GET /api/onboard/status
Get current onboarding status and next steps.

**Response:**
```json
{
  "success": true,
  "onboarding_status": {
    "current_status": "Verified",
    "docs_uploaded": true,
    "has_pan": true,
    "has_gst": true,
    "whatsapp_connected": true,
    "approved_templates": 2,
    "can_send_messages": true,
    "next_steps": [],
    "completion_percentage": 100
  }
}
```

---

## Error Codes

- `400` - Bad Request (validation errors, missing fields)
- `401` - Unauthorized (not logged in, invalid credentials)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found (resource doesn't exist)
- `500` - Internal Server Error

## Rate Limiting
- Message sending is limited by user's monthly quota
- Bulk operations are limited to prevent abuse
- File uploads are limited to 16MB per file

## File Upload Constraints
- **Allowed formats:** PDF, JPG, PNG, JPEG
- **Maximum size:** 16MB per file
- **Document types:** PAN, GST for business verification

## WhatsApp Integration Notes
- Templates must be approved by Meta before use
- Message delivery status is updated via webhooks
- Phone numbers must include country code (e.g., 919876543210)
- Templates support variables, headers, footers, and buttons