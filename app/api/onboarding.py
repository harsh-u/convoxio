import logging
import requests
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from app.models import User, Template

logger = logging.getLogger(__name__)

onboarding_api = Blueprint('onboarding_api', __name__)

@onboarding_api.route('/onboard/start', methods=['POST'])
@login_required
def start_onboarding():
    """Start WhatsApp Business onboarding process"""
    try:
        # Generate Meta OAuth URL
        oauth_url = (
            f"https://www.facebook.com/v19.0/dialog/oauth?"
            f"client_id={current_app.config['META_APP_ID']}&"
            f"redirect_uri={current_app.config['META_REDIRECT_URI']}&"
            f"scope={current_app.config['META_PERMISSIONS']}&"
            f"state={current_user.id}"
        )
        
        logger.info(f"🔗 OAuth URL generated for user {current_user.id}")
        
        return jsonify({
            'success': True,
            'oauth_url': oauth_url,
            'message': 'Redirect user to this URL to complete WhatsApp setup'
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Start onboarding error: {str(e)}")
        return jsonify({'error': 'Failed to start onboarding process'}), 500

@onboarding_api.route('/onboard/simple-setup', methods=['POST'])
@login_required
def simple_setup():
    """Simple WhatsApp setup for small businesses"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('whatsapp_number') or not data.get('otp'):
            return jsonify({'error': 'WhatsApp number and OTP are required'}), 400
        
        phone_number = data['whatsapp_number']
        otp = data['otp']
        
        # Validate phone number format
        if not phone_number or len(phone_number) < 10:
            return jsonify({
                'error': 'Please enter a valid WhatsApp number with country code (e.g., 919876543210)'
            }), 400
        
        # Demo OTP verification - in production, verify real SMS OTP
        if otp == '123456':
            # Instantly activate user with platform credentials
            current_user.onboarding_status = 'Verified'
            current_user.phone_number = phone_number
            
            # Use platform's WhatsApp Business API credentials
            current_user.waba_id = 'platform_waba_id_123'
            current_user.phone_number_id = assign_dedicated_whatsapp_number(
                current_user.id, 
                current_user.business_name or 'Business'
            )
            current_user.whatsapp_access_token = 'platform_access_token_789'
            
            # Create starter templates automatically
            auto_create_starter_templates(current_user.id)
            
            db.session.commit()
            
            logger.info(f"✅ Simple setup completed for user {current_user.id}")
            
            return jsonify({
                'success': True,
                'message': 'Setup complete! You can now send WhatsApp messages to your customers.',
                'user': {
                    'id': current_user.id,
                    'onboarding_status': current_user.onboarding_status,
                    'waba_id': current_user.waba_id,
                    'phone_number_id': current_user.phone_number_id,
                    'phone_number': current_user.phone_number
                }
            }), 200
        else:
            return jsonify({
                'error': 'Invalid verification code. Please try 123456 for demo.'
            }), 400
            
    except Exception as e:
        logger.error(f"❌ Simple setup error: {str(e)}")
        return jsonify({'error': 'Failed to complete setup'}), 500

@onboarding_api.route('/onboard/update-credentials', methods=['POST'])
@login_required
def update_whatsapp_credentials():
    """Update WhatsApp credentials manually (for testing)"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['access_token', 'waba_id', 'phone_id']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Update user credentials
        current_user.whatsapp_access_token = data['access_token'].strip()
        current_user.waba_id = data['waba_id'].strip()
        current_user.phone_number_id = data['phone_id'].strip()
        current_user.onboarding_status = 'Verified'
        
        db.session.commit()
        
        logger.info(f"✅ WhatsApp credentials updated for user {current_user.id}")
        
        return jsonify({
            'success': True,
            'message': 'WhatsApp credentials updated successfully',
            'user': {
                'id': current_user.id,
                'onboarding_status': current_user.onboarding_status,
                'waba_id': current_user.waba_id,
                'phone_number_id': current_user.phone_number_id
            }
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Update credentials error: {str(e)}")
        return jsonify({'error': 'Failed to update credentials'}), 500

@onboarding_api.route('/onboard/reset', methods=['POST'])
@login_required
def reset_whatsapp_connection():
    """Reset WhatsApp connection for testing"""
    try:
        current_user.whatsapp_access_token = None
        current_user.waba_id = None
        current_user.phone_number_id = None
        current_user.onboarding_status = 'Pending'
        
        db.session.commit()
        
        logger.info(f"🔄 WhatsApp connection reset for user {current_user.id}")
        
        return jsonify({
            'success': True,
            'message': 'WhatsApp connection reset. You can set it up again.',
            'user': {
                'id': current_user.id,
                'onboarding_status': current_user.onboarding_status
            }
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Reset connection error: {str(e)}")
        return jsonify({'error': 'Failed to reset connection'}), 500

@onboarding_api.route('/onboard/status', methods=['GET'])
@login_required
def get_onboarding_status():
    """Get current onboarding status and next steps"""
    try:
        from app.models import Upload
        
        # Check document upload status
        uploads = Upload.query.filter_by(user_id=current_user.id).all()
        has_pan = any(u.filetype == 'PAN' for u in uploads)
        has_gst = any(u.filetype == 'GST' for u in uploads)
        docs_uploaded = has_pan and has_gst
        
        # Check template status
        approved_templates = Template.query.filter_by(
            user_id=current_user.id, 
            status='Approved'
        ).count()
        
        # Determine next steps
        next_steps = []
        if not docs_uploaded:
            next_steps.append({
                'step': 'upload_documents',
                'title': 'Upload Business Documents',
                'description': 'Upload PAN and GST documents for verification (optional)',
                'required': False
            })
        
        if current_user.onboarding_status != 'Verified':
            next_steps.append({
                'step': 'connect_whatsapp',
                'title': 'Connect WhatsApp Business',
                'description': 'Link your WhatsApp Business account to start messaging',
                'required': True
            })
        
        if current_user.onboarding_status == 'Verified' and approved_templates == 0:
            next_steps.append({
                'step': 'create_templates',
                'title': 'Create Message Templates',
                'description': 'Create and get approval for your first message templates',
                'required': True
            })
        
        return jsonify({
            'success': True,
            'onboarding_status': {
                'current_status': current_user.onboarding_status,
                'docs_uploaded': docs_uploaded,
                'has_pan': has_pan,
                'has_gst': has_gst,
                'whatsapp_connected': current_user.onboarding_status == 'Verified',
                'approved_templates': approved_templates,
                'can_send_messages': (
                    current_user.onboarding_status == 'Verified' and 
                    approved_templates > 0
                ),
                'next_steps': next_steps,
                'completion_percentage': calculate_completion_percentage(
                    docs_uploaded, 
                    current_user.onboarding_status == 'Verified',
                    approved_templates > 0
                )
            }
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Get onboarding status error: {str(e)}")
        return jsonify({'error': 'Failed to get onboarding status'}), 500

def assign_dedicated_whatsapp_number(user_id, business_name):
    """Assign a dedicated WhatsApp number to the user (mock implementation)"""
    # In a real implementation, this would:
    # 1. Request a new phone number from your WhatsApp Business provider
    # 2. Configure the number for the user's business
    # 3. Return the phone number ID
    
    # For demo purposes, generate a mock phone number ID
    import hashlib
    hash_input = f"{user_id}_{business_name}".encode()
    phone_id = hashlib.md5(hash_input).hexdigest()[:15]
    
    logger.info(f"📞 Assigned phone number ID {phone_id} to user {user_id}")
    return f"phone_{phone_id}"

def auto_create_starter_templates(user_id):
    """Automatically create starter templates for new users"""
    try:
        starter_templates = [
            {
                'name': 'welcome_message',
                'language': 'en_US',
                'content': 'Welcome to {{business_name}}! We\'re excited to serve you.',
                'category': 'TRANSACTIONAL',
                'status': 'Approved'  # Auto-approve for demo
            },
            {
                'name': 'order_confirmation',
                'language': 'en_US', 
                'content': 'Your order #{{order_id}} has been confirmed. Thank you for your business!',
                'category': 'TRANSACTIONAL',
                'status': 'Approved'  # Auto-approve for demo
            },
            {
                'name': 'appointment_reminder',
                'language': 'en_US',
                'content': 'Reminder: You have an appointment scheduled for {{date}} at {{time}}.',
                'category': 'UTILITY',
                'status': 'Approved'  # Auto-approve for demo
            }
        ]
        
        for template_data in starter_templates:
            template = Template(
                user_id=user_id,
                name=template_data['name'],
                language=template_data['language'],
                content=template_data['content'],
                category=template_data['category'],
                status=template_data['status'],
                header_type='NONE'
            )
            db.session.add(template)
        
        db.session.commit()
        logger.info(f"✅ Created {len(starter_templates)} starter templates for user {user_id}")
        
    except Exception as e:
        logger.error(f"❌ Error creating starter templates: {str(e)}")

@onboarding_api.route('/onboard/support-request', methods=['POST'])
@login_required
def submit_support_request():
    """Handle support request form submission for manual WhatsApp setup"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['business_name', 'business_type', 'contact_person', 'whatsapp_number', 'business_address', 'business_description']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Create support request record (you can create a new model for this)
        support_request_data = {
            'user_id': current_user.id,
            'business_name': data['business_name'],
            'business_type': data['business_type'],
            'contact_person': data['contact_person'],
            'whatsapp_number': data['whatsapp_number'],
            'business_address': data['business_address'],
            'website': data.get('website', ''),
            'business_description': data['business_description'],
            'status': 'pending',
            'created_at': datetime.now()
        }
        
        # Update user's onboarding status to "In Progress"
        current_user.onboarding_status = 'In Progress'
        
        # Update user's business information
        if data['business_name']:
            current_user.business_name = data['business_name']
        if data['whatsapp_number']:
            current_user.phone_number = data['whatsapp_number']
        
        db.session.commit()
        
        # Log the support request (in a real app, you'd save this to a SupportRequest model)
        logger.info(f"📋 Support request submitted by user {current_user.id}: {support_request_data}")
        
        # In a real implementation, you would:
        # 1. Save to SupportRequest model
        # 2. Send email notification to support team
        # 3. Create a ticket in your support system
        # 4. Send confirmation email to user
        
        # For now, we'll simulate this by logging and updating user status
        logger.info(f"✅ Support request processed for user {current_user.id} - {data['business_name']}")
        
        return jsonify({
            'success': True,
            'message': 'Support request submitted successfully! Our team will contact you within 24 hours.',
            'request_id': f"REQ-{current_user.id}-{int(datetime.now().timestamp())}",
            'estimated_completion': '1-2 business days'
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Support request error: {str(e)}")
        return jsonify({'error': 'Failed to submit support request'}), 500

def calculate_completion_percentage(docs_uploaded, whatsapp_connected, has_templates):
    """Calculate onboarding completion percentage"""
    total_steps = 3
    completed_steps = 0
    
    if docs_uploaded:
        completed_steps += 1
    if whatsapp_connected:
        completed_steps += 1
    if has_templates:
        completed_steps += 1
    
    return round((completed_steps / total_steps) * 100)