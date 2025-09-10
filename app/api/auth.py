import logging
from flask import Blueprint, request, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models import User

logger = logging.getLogger(__name__)

auth_api = Blueprint('auth_api', __name__)

@auth_api.route('/register', methods=['POST'])
def register():
    """User registration API"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['business_name', 'email', 'phone_number', 'password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        logger.info(f"📝 API registration attempt for email: {data.get('email')}")
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=data['email']).first()
        if existing_user:
            logger.warning(f"⚠️ API registration failed - email already exists: {data['email']}")
            return jsonify({'error': 'Email already registered. Please use a different email or login.'}), 400
        
        # Create new user
        hashed_pw = generate_password_hash(data['password'])
        user = User(
            business_name=data['business_name'],
            email=data['email'],
            phone_number=data['phone_number'],
            password=hashed_pw,
            message_limit=1000  # Default limit for new users
        )
        
        db.session.add(user)
        db.session.commit()
        logger.info(f"✅ New user registered successfully: {user.email} (ID: {user.id})")
        
        # Auto-login the user after registration
        login_user(user)
        logger.info(f"🔐 User auto-logged in after registration: {user.email}")
        
        return jsonify({
            'success': True,
            'message': 'Registration successful',
            'user': {
                'id': user.id,
                'email': user.email,
                'business_name': user.business_name,
                'phone_number': user.phone_number,
                'onboarding_status': user.onboarding_status,
                'message_limit': user.message_limit,
                'messages_sent_this_month': user.messages_sent_this_month
            }
        }), 201
        
    except Exception as e:
        logger.error(f"❌ Registration error: {str(e)}")
        return jsonify({'error': 'Registration failed. Please try again.'}), 500

@auth_api.route('/login', methods=['POST'])
def login():
    """User login API"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password are required'}), 400
        
        logger.info(f"🔐 API login attempt for email: {data.get('email')}")
        
        user = User.query.filter_by(email=data['email']).first()
        
        if user and check_password_hash(user.password, data['password']):
            login_user(user)
            logger.info(f"✅ API user logged in successfully: {user.email} (ID: {user.id})")
            
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'business_name': user.business_name,
                    'phone_number': user.phone_number,
                    'onboarding_status': user.onboarding_status,
                    'message_limit': user.message_limit,
                    'messages_sent_this_month': user.messages_sent_this_month,
                    'waba_id': user.waba_id,
                    'phone_number_id': user.phone_number_id,
                    'is_verified': user.is_verified
                }
            }), 200
        
        logger.warning(f"❌ Failed API login attempt for email: {data.get('email')}")
        return jsonify({'error': 'Invalid credentials'}), 401
        
    except Exception as e:
        logger.error(f"❌ Login error: {str(e)}")
        return jsonify({'error': 'Login failed. Please try again.'}), 500

@auth_api.route('/logout', methods=['POST'])
@login_required
def logout():
    """User logout API"""
    try:
        logger.info(f"🚪 API User logout: {current_user.email} (ID: {current_user.id})")
        logout_user()
        logger.info("✅ User logged out successfully")
        
        return jsonify({
            'success': True,
            'message': 'Logout successful'
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Logout error: {str(e)}")
        return jsonify({'error': 'Logout failed'}), 500

@auth_api.route('/user/status', methods=['GET'])
@login_required
def get_user_status():
    """Get current user status and details"""
    try:
        return jsonify({
            'success': True,
            'user': {
                'id': current_user.id,
                'email': current_user.email,
                'business_name': current_user.business_name,
                'phone_number': current_user.phone_number,
                'onboarding_status': current_user.onboarding_status,
                'message_limit': current_user.message_limit,
                'messages_sent_this_month': current_user.messages_sent_this_month,
                'remaining_messages': current_user.get_remaining_messages(),
                'waba_id': current_user.waba_id,
                'phone_number_id': current_user.phone_number_id,
                'is_verified': current_user.is_verified,
                'can_send_message': current_user.can_send_message(),
                'is_premium': current_user.is_premium()
            }
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Get user status error: {str(e)}")
        return jsonify({'error': 'Failed to get user status'}), 500

@auth_api.route('/user/profile', methods=['PUT'])
@login_required
def update_profile():
    """Update user profile"""
    try:
        data = request.get_json()
        
        # Update allowed fields
        if data.get('business_name'):
            current_user.business_name = data['business_name']
        if data.get('phone_number'):
            current_user.phone_number = data['phone_number']
        
        db.session.commit()
        logger.info(f"✅ Profile updated for user: {current_user.email}")
        
        return jsonify({
            'success': True,
            'message': 'Profile updated successfully',
            'user': {
                'id': current_user.id,
                'email': current_user.email,
                'business_name': current_user.business_name,
                'phone_number': current_user.phone_number
            }
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Profile update error: {str(e)}")
        return jsonify({'error': 'Failed to update profile'}), 500