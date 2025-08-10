import logging
from flask import Blueprint, request, jsonify, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import json
import requests
from app import db
from app.models import User, Upload, Template, MessageHistory
from app.forms import RegisterForm, LoginForm, UploadForm, WhatsAppMessageForm, TemplateForm
from app import login_manager

# Create logger for API routes
logger = logging.getLogger(__name__)

api = Blueprint('api', __name__)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@api.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    logger.info(f"🔗 API registration attempt for email: {data.get('email', 'N/A')}")
    
    if User.query.filter_by(email=data['email']).first():
        logger.warning(f"⚠️ API registration failed - email already exists: {data['email']}")
        return jsonify({'error': 'Email already registered'}), 400
    
    user = User(
        email=data['email'],
        password=generate_password_hash(data['password'])
    )
    db.session.add(user)
    db.session.commit()
    logger.info(f"✅ API user registered successfully: {user.email} (ID: {user.id})")
    
    return jsonify({'message': 'Registration successful', 'user_id': user.id}), 201

@api.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    logger.info(f"🔗 API login attempt for email: {data.get('email', 'N/A')}")
    user = User.query.filter_by(email=data['email']).first()
    
    if user and check_password_hash(user.password, data['password']):
        login_user(user)
        logger.info(f"✅ API user logged in successfully: {user.email} (ID: {user.id})")
        return jsonify({
            'message': 'Login successful',
            'user': {
                'id': user.id,
                'email': user.email,
                'onboarding_status': user.onboarding_status
            }
        })
    
    logger.warning(f"❌ Failed API login attempt for email: {data.get('email', 'N/A')}")
    return jsonify({'error': 'Invalid credentials'}), 401

@api.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'Logout successful'})

@api.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    uploads = Upload.query.filter_by(user_id=current_user.id).all()
    docs_uploaded = len(uploads) >= 2
    
    templates = Template.query.filter_by(user_id=current_user.id, status='Approved').all()
    message_history = MessageHistory.query.filter_by(user_id=current_user.id).order_by(MessageHistory.created_at.desc()).limit(10).all()
    
    can_send = current_user.onboarding_status == 'Verified'
    
    return jsonify({
        'user': {
            'id': current_user.id,
            'email': current_user.email,
            'onboarding_status': current_user.onboarding_status
        },
        'docs_uploaded': docs_uploaded,
        'uploads': [{'id': u.id, 'filename': u.filename, 'filetype': u.filetype} for u in uploads],
        'templates': [{'id': t.id, 'name': t.name, 'status': t.status} for t in templates],
        'message_history': [{
            'id': m.id,
            'recipient': m.recipient,
            'template_id': m.template_id,
            'status': m.status,
            'created_at': m.created_at.isoformat()
        } for m in message_history],
        'can_send': can_send
    })

@api.route('/upload', methods=['POST'])
@login_required
def upload_documents():
    if 'pan_file' not in request.files and 'gst_file' not in request.files:
        return jsonify({'error': 'No files provided'}), 400
    
    uploads = []
    
    for file_key in ['pan_file', 'gst_file']:
        if file_key in request.files:
            file = request.files[file_key]
            if file.filename == '':
                continue
                
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filetype = 'PAN' if file_key == 'pan_file' else 'GST'
                
                # Save file
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                
                # Create upload record
                upload = Upload(
                    filename=filename,
                    filetype=filetype,
                    user_id=current_user.id
                )
                db.session.add(upload)
                uploads.append(upload)
    
    if uploads:
        db.session.commit()
        return jsonify({'message': 'Documents uploaded successfully', 'uploads': len(uploads)})
    
    return jsonify({'error': 'No valid files uploaded'}), 400

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@api.route('/onboard/start', methods=['GET'])
@login_required
def start_onboarding():
    # Check if documents are uploaded
    uploads = Upload.query.filter_by(user_id=current_user.id).all()
    if len(uploads) < 2:
        return jsonify({'error': 'Please upload both PAN and GST documents first'}), 400
    
    # Generate Meta OAuth URL
    oauth_url = f"https://www.facebook.com/v18.0/dialog/oauth?client_id={current_app.config['META_APP_ID']}&redirect_uri={current_app.config['META_REDIRECT_URI']}&scope={current_app.config['META_PERMISSIONS']}&state={current_user.id}"
    
    return jsonify({'oauth_url': oauth_url})

@api.route('/onboard/callback', methods=['GET'])
def onboarding_callback():
    code = request.args.get('code')
    state = request.args.get('state')
    
    if not code or not state:
        return jsonify({'error': 'Missing authorization code'}), 400
    
    # Exchange code for access token
    token_url = "https://graph.facebook.com/v18.0/oauth/access_token"
    token_data = {
        'client_id': current_app.config['META_APP_ID'],
        'client_secret': current_app.config['META_APP_SECRET'],
        'redirect_uri': current_app.config['META_REDIRECT_URI'],
        'code': code
    }
    
    response = requests.post(token_url, data=token_data)
    if response.status_code != 200:
        return jsonify({'error': 'Failed to get access token'}), 400
    
    token_info = response.json()
    access_token = token_info.get('access_token')
    
    # Get WhatsApp Business Account info
    waba_url = "https://graph.facebook.com/v18.0/me/whatsapp_business_accounts"
    headers = {'Authorization': f'Bearer {access_token}'}
    
    waba_response = requests.get(waba_url, headers=headers)
    if waba_response.status_code == 200:
        waba_data = waba_response.json()
        if waba_data.get('data'):
            waba_id = waba_data['data'][0]['id']
            
            # Get phone number ID
            phone_url = f"https://graph.facebook.com/v18.0/{waba_id}/phone_numbers"
            phone_response = requests.get(phone_url, headers=headers)
            
            if phone_response.status_code == 200:
                phone_data = phone_response.json()
                if phone_data.get('data'):
                    phone_number_id = phone_data['data'][0]['id']
                    
                    # Update user with WhatsApp credentials
                    user = User.query.get(int(state))
                    if user:
                        user.waba_id = waba_id
                        user.phone_number_id = phone_number_id
                        user.whatsapp_access_token = access_token
                        user.onboarding_status = 'Verified'
                        db.session.commit()
                        
                        return jsonify({'message': 'WhatsApp onboarding completed successfully'})
    
    return jsonify({'error': 'Failed to complete WhatsApp onboarding'}), 400

@api.route('/templates', methods=['GET'])
@login_required
def get_templates():
    templates = Template.query.filter_by(user_id=current_user.id).all()
    return jsonify({
        'templates': [{
            'id': t.id,
            'name': t.name,
            'language': t.language,
            'content': t.content,
            'status': t.status,
            'category': t.category,
            'header_type': t.header_type,
            'header_text': t.header_text,
            'header_image_url': t.header_image_url,
            'footer_text': t.footer_text,
            'buttons_json': t.buttons_json,
            'created_at': t.created_at.isoformat()
        } for t in templates]
    })

@api.route('/templates', methods=['POST'])
@login_required
def create_template():
    data = request.get_json()
    
    # Prepare buttons JSON
    buttons = []
    for i in range(1, 4):
        if data.get(f'button{i}_type') and data.get(f'button{i}_text'):
            button = {
                'type': data[f'button{i}_type'],
                'text': data[f'button{i}_text']
            }
            if data.get(f'button{i}_url'):
                button['url'] = data[f'button{i}_url']
            buttons.append(button)
    
    template = Template(
        user_id=current_user.id,
        name=data['name'],
        language=data['language'],
        content=data['content'],
        category=data['category'],
        header_type=data.get('header_type', 'NONE'),
        header_text=data.get('header_text'),
        header_image_url=data.get('header_image_url'),
        footer_text=data.get('footer_text'),
        buttons_json=json.dumps(buttons) if buttons else None
    )
    
    db.session.add(template)
    db.session.commit()
    
    # Submit to Meta for approval
    if current_user.whatsapp_access_token:
        meta_template_data = {
            'name': template.name,
            'language': template.language,
            'category': template.category,
            'components': []
        }
        
        # Add header component
        if template.header_type != 'NONE':
            header_component = {
                'type': 'HEADER',
                'format': template.header_type.lower()
            }
            if template.header_type == 'TEXT':
                header_component['text'] = template.header_text
            elif template.header_type == 'IMAGE':
                header_component['example'] = {'header_handle': [template.header_image_url]}
            meta_template_data['components'].append(header_component)
        
        # Add body component
        body_component = {
            'type': 'BODY',
            'text': template.content
        }
        meta_template_data['components'].append(body_component)
        
        # Add footer component
        if template.footer_text:
            footer_component = {
                'type': 'FOOTER',
                'text': template.footer_text
            }
            meta_template_data['components'].append(footer_component)
        
        # Add buttons
        if buttons:
            buttons_component = {
                'type': 'BUTTONS',
                'buttons': buttons
            }
            meta_template_data['components'].append(buttons_component)
        
        # Submit to Meta
        meta_url = f"https://graph.facebook.com/v18.0/{current_user.waba_id}/message_templates"
        headers = {
            'Authorization': f'Bearer {current_user.whatsapp_access_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            meta_response = requests.post(meta_url, json=meta_template_data, headers=headers)
            print(f"Meta response: {meta_response.json()}")
            if meta_response.status_code == 200:
                meta_data = meta_response.json()
                template.meta_template_id = meta_data.get('id')
                template.status = 'Pending'
                db.session.commit()
        except Exception as e:
            template.status = 'Rejected'
            db.session.commit()
    
    return jsonify({
        'message': 'Template created successfully',
        'template': {
            'id': template.id,
            'name': template.name,
            'status': template.status
        }
    }), 201

@api.route('/send-message', methods=['POST'])
@login_required
def send_message():
    if current_user.onboarding_status != 'Verified':
        return jsonify({'error': 'WhatsApp onboarding not completed'}), 400
    
    data = request.get_json()
    template = Template.query.get(data['template_id'])
    
    if not template or template.user_id != current_user.id:
        return jsonify({'error': 'Template not found'}), 404
    
    # Send message via WhatsApp API
    message_data = {
        'messaging_product': 'whatsapp',
        'to': data['recipient'],
        'type': 'template',
        'template': {
            'name': template.name,
            'language': {
                'code': data.get('language', 'en_US')
            }
        }
    }
    
    print(f"message_data :: {message_data}")
    
    url = f"https://graph.facebook.com/v18.0/{current_user.phone_number_id}/messages"
    headers = {
        'Authorization': f'Bearer {current_user.whatsapp_access_token}',
        'Content-Type': 'application/json'
    }
    print(f"url :: {url}")
    print(f"headers :: {headers}")
    try:
        response = requests.post(url, json=message_data, headers=headers)
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            
            # Save message history
            message = MessageHistory(
                user_id=current_user.id,
                recipient=data['recipient'],
                template_id=template.id,
                meta_message_id=result.get('messages', [{}])[0].get('id'),
                status='sent'
            )
            db.session.add(message)
            db.session.commit()
            
            return jsonify({'message': 'Message sent successfully'})
        else:
            error_response = response.json()
            return jsonify({'error': error_response}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api.route('/webhook/meta', methods=['POST', 'GET'])
def meta_webhook():
    print(f"Webhook called with method: {request.method}")
    print(f"Request args: {dict(request.args)}")
    
    # Handle webhook verification (GET request)
    if request.method == 'GET':
        print("Handling webhook verification...")
        if request.args.get('hub.mode') == 'subscribe':
            verify_token = request.args.get('hub.verify_token')
            challenge = request.args.get('hub.challenge')
            print(f"Verify token: {verify_token}")
            print(f"Challenge: {challenge}")
            
            if verify_token == '12345':
                print("Webhook verification successful")
                return challenge
            else:
                print("Webhook verification failed - invalid token")
                return 'Forbidden', 403
        return 'OK', 200
    
    # Handle webhook data (POST request)
    if request.method == 'POST':
        print("Handling webhook POST request...")
        data = request.get_json()
        print(f"Webhook data received: {data}")
        
        # Handle status updates
        if data and data.get('entry'):
            for entry in data['entry']:
                for change in entry.get('changes', []):
                    if change.get('value', {}).get('statuses'):
                        for status in change['value']['statuses']:
                            message_id = status.get('id')
                            message_status = status.get('status')
                            
                            print(f"Message status update: {message_id} -> {message_status}")
                            
                            # Update message history
                            message = MessageHistory.query.filter_by(meta_message_id=message_id).first()
                            if message:
                                message.status = message_status
                                db.session.commit()
                                print(f"Updated message {message_id} status to {message_status}")
                            else:
                                print(f"Message {message_id} not found in database")
        
        return jsonify({'status': 'ok'})
    
    return jsonify({'status': 'ok'})

@api.route('/user/status', methods=['GET'])
@login_required
def get_user_status():
    return jsonify({
        'user': {
            'id': current_user.id,
            'email': current_user.email,
            'onboarding_status': current_user.onboarding_status
        }
    })