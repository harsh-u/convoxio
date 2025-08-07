import os
from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app as app
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import requests                                 
from app import db, login_manager
from app.models import User, Upload, Template, MessageHistory
from app.forms import RegisterForm, LoginForm, UploadForm, WhatsAppMessageForm, TemplateForm
from config import Config
import urllib.parse
from wtforms import SelectField

main = Blueprint('main', __name__)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('Email already registered. Please use a different email or login.', 'danger')
            return redirect(url_for('main.register'))
        
        hashed_pw = generate_password_hash(form.password.data)
        user = User(
            business_name=form.business_name.data,
            email=form.email.data,
            phone_number=form.phone_number.data,
            password=hashed_pw,
            message_limit=1000  # Default limit for new users
        )
        db.session.add(user)
        db.session.commit()
        
        # Auto-login the user after registration
        login_user(user)
        flash('Welcome to Convoxio! Let\'s get your account set up.', 'success')
        return redirect(url_for('main.dashboard'))
    return render_template('register.html', form=form)

@main.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('main.dashboard'))
        flash('Invalid credentials', 'danger')
    return render_template('login.html', form=form)

@main.route('/dashboard')
@login_required
def dashboard():
    uploads = Upload.query.filter_by(user_id=current_user.id).all()
    has_pan = any(u.filetype == 'PAN' for u in uploads)
    has_gst = any(u.filetype == 'GST' for u in uploads)
    docs_uploaded = has_pan and has_gst
    onboarding_status = current_user.onboarding_status
    
    # Check if user can send messages
    approved_templates = Template.query.filter_by(user_id=current_user.id, status='Approved').all()
    can_send = (onboarding_status == 'Verified' and 
                current_user.whatsapp_access_token and 
                current_user.phone_number_id and 
                approved_templates)
    
    # Get recent message history
    message_history = MessageHistory.query.filter_by(user_id=current_user.id).order_by(MessageHistory.created_at.desc()).limit(10).all()
    
    return render_template('dashboard.html', 
                           docs_uploaded=docs_uploaded,
                           can_send=can_send,
                           onboarding_status=onboarding_status,
                           message_history=message_history)

@main.route('/dashboard/templates', methods=['GET', 'POST'])
@login_required
def manage_templates():
    form = TemplateForm()
    if form.validate_on_submit():
        # Build components array for Meta API
        components = []
        # Header
        if form.header_type.data == 'TEXT' and form.header_text.data:
            components.append({"type": "HEADER", "format": "TEXT", "text": form.header_text.data})
        elif form.header_type.data == 'IMAGE' and form.header_image_url.data:
            components.append({"type": "HEADER", "format": "IMAGE", "example": {"header_handle": form.header_image_url.data}})
        # Body (always required)
        components.append({"type": "BODY", "text": form.content.data})
        # Footer
        if form.footer_text.data:
            components.append({"type": "FOOTER", "text": form.footer_text.data})
        # Buttons (build from form fields)
        buttons = []
        for i in range(1, 4):
            btn_type = getattr(form, f'button{i}_type').data
            btn_text = getattr(form, f'button{i}_text').data
            btn_url = getattr(form, f'button{i}_url').data
            if btn_type == 'QUICK_REPLY' and btn_text:
                buttons.append({"type": "QUICK_REPLY", "text": btn_text})
            elif btn_type == 'CALL_TO_ACTION' and btn_text:
                btn = {"type": "CALL_TO_ACTION", "text": btn_text, "url": btn_url} if btn_url else {"type": "CALL_TO_ACTION", "text": btn_text}
                buttons.append(btn)
        if buttons:
            components.append({"type": "BUTTONS", "buttons": buttons})
        import json
        buttons_json_str = json.dumps(buttons) if buttons else None
        # Submit to Meta first
        try:
            url = f"https://graph.facebook.com/v19.0/{current_user.waba_id}/message_templates"
            headers = {"Authorization": f"Bearer {current_user.whatsapp_access_token}"}
            payload = {
                "name": form.name.data,
                "language": {"code": form.language.data},
                "components": components,
                "category": form.category.data
            }
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                resp_json = response.json()
                template = Template(
                    user_id=current_user.id,
                    name=form.name.data,
                    language=form.language.data,
                    content=form.content.data,
                    status='Pending',
                    meta_template_id=resp_json.get("id"),
                    category=form.category.data,
                    header_type=form.header_type.data,
                    header_text=form.header_text.data,
                    header_image_url=form.header_image_url.data,
                    footer_text=form.footer_text.data,
                    buttons_json=buttons_json_str
                )
                db.session.add(template)
                db.session.commit()
                flash('Template submitted to Meta for approval!', 'success')
            else:
                flash(f"Meta API error: {response.status_code} {response.text}", 'danger')
        except Exception as e:
            flash(f"Error submitting template to Meta: {e}", 'danger')
        return redirect(url_for('main.manage_templates'))
    templates = Template.query.filter_by(user_id=current_user.id).order_by(Template.created_at.desc()).all()
    return render_template('manage_templates.html', form=form, templates=templates)



@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))

@main.route('/verify-phone', methods=['GET', 'POST'])
@login_required
def verify_phone():
    if request.method == 'POST':
        # For now, we'll simulate phone verification
        # In production, you'd send SMS OTP here
        phone_number = request.form.get('phone_number')
        otp = request.form.get('otp')
        
        if otp == '123456':  # Demo OTP
            # Mark user as verified and ready to send messages
            current_user.onboarding_status = 'Verified'
            current_user.phone_number = phone_number
            # Use your platform's WhatsApp credentials
            current_user.waba_id = 'your_platform_waba_id'
            current_user.phone_number_id = 'your_platform_phone_id'
            current_user.whatsapp_access_token = 'your_platform_token'
            
            db.session.commit()
            flash('Phone verified! You can now start sending WhatsApp messages.', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash('Invalid OTP. Please try again.', 'danger')
    
    return render_template('verify_phone.html')

@main.route('/reset-whatsapp')
@login_required
def reset_whatsapp():
    """Reset WhatsApp connection for testing"""
    current_user.whatsapp_access_token = None
    current_user.waba_id = None
    current_user.phone_number_id = None
    current_user.onboarding_status = 'Pending'
    db.session.commit()
    flash('WhatsApp connection reset. You can set it up again.', 'info')
    return redirect(url_for('main.simple_setup'))

@main.route('/debug-user')
@login_required
def debug_user():
    """Debug route to check current user data"""
    # Force refresh user from database
    db.session.refresh(current_user)
    
    print(f"🔍 DEBUG USER DATA:")
    print(f"  - ID: {current_user.id}")
    print(f"  - Email: {current_user.email}")
    print(f"  - WABA ID: {current_user.waba_id}")
    print(f"  - Phone ID: {current_user.phone_number_id}")
    print(f"  - Token (first 50): {current_user.whatsapp_access_token[:50] if current_user.whatsapp_access_token else 'None'}")
    print(f"  - Status: {current_user.onboarding_status}")
    
    return f"""
    <h2>Debug User Data</h2>
    <p><strong>ID:</strong> {current_user.id}</p>
    <p><strong>Email:</strong> {current_user.email}</p>
    <p><strong>WABA ID:</strong> {current_user.waba_id}</p>
    <p><strong>Phone ID:</strong> {current_user.phone_number_id}</p>
    <p><strong>Token (first 50):</strong> {current_user.whatsapp_access_token[:50] if current_user.whatsapp_access_token else 'None'}</p>
    <p><strong>Status:</strong> {current_user.onboarding_status}</p>
    <p><a href="/dashboard">Back to Dashboard</a></p>
    <p><a href="/force-refresh-user">Force Refresh User Data</a></p>
    """

@main.route('/force-refresh-user')
@login_required
def force_refresh_user():
    """Force refresh user data from database"""
    # Clear SQLAlchemy session and reload user
    db.session.expunge(current_user)
    db.session.commit()
    fresh_user = User.query.get(current_user.id)
    
    # Update current_user object with fresh data
    current_user.waba_id = fresh_user.waba_id
    current_user.phone_number_id = fresh_user.phone_number_id
    current_user.whatsapp_access_token = fresh_user.whatsapp_access_token
    current_user.onboarding_status = fresh_user.onboarding_status
    
    flash('User data refreshed from database', 'info')
    return redirect(url_for('main.debug_user'))

@main.route('/update-token', methods=['GET', 'POST'])
@login_required
def update_token():
    """Quick way to update WhatsApp access token for testing"""
    if request.method == 'POST':
        new_token = request.form.get('access_token', '').strip()
        waba_id = request.form.get('waba_id', '').strip()
        phone_id = request.form.get('phone_id', '').strip()
        
        if new_token and waba_id and phone_id:
            current_user.whatsapp_access_token = new_token
            current_user.waba_id = waba_id
            current_user.phone_number_id = phone_id
            current_user.onboarding_status = 'Verified'
            db.session.commit()
            flash('WhatsApp credentials updated successfully!', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash('Please fill in all fields.', 'danger')
    
    return render_template('update_token.html')

@main.route('/simple-setup', methods=['GET', 'POST'])
@login_required
def simple_setup():
    """Ultra-simple setup for small businesses - just verify their WhatsApp number"""
    if request.method == 'POST':
        phone_number = request.form.get('whatsapp_number')
        otp = request.form.get('otp')
        
        # Validate phone number format
        if not phone_number or len(phone_number) < 10:
            flash('Please enter a valid WhatsApp number with country code (e.g., 919876543210)', 'danger')
            return render_template('simple_setup.html')
        
        if otp == '123456':  # Demo OTP - in production, send real SMS
            # Instantly activate user with platform credentials
            current_user.onboarding_status = 'Verified'
            current_user.phone_number = phone_number
            
            # Use platform's WhatsApp Business API credentials
            current_user.waba_id = 'platform_waba_id_123'
            current_user.phone_number_id = assign_dedicated_whatsapp_number(current_user.id, current_user.business_name or 'Business')
            current_user.whatsapp_access_token = 'platform_access_token_789'
            
            # Give them some starter templates automatically
            auto_create_starter_templates(current_user.id)
            
            db.session.commit()
            
            flash('🎉 Setup complete! You can now send WhatsApp messages to your customers.', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash('Invalid verification code. Please try 123456 for demo.', 'danger')
    
    return render_template('simple_setup.html')

@main.route('/onboard/callback')
def onboard_callback():
    import requests
    import json
    from flask import request

    code = request.args.get('code')
    user_id = request.args.get('state')  # state = user_id

    if not code:
        flash("Meta did not return a code", "danger")
        return redirect(url_for('main.dashboard'))

    token_url = "https://graph.facebook.com/v19.0/oauth/access_token"
    params = {
        "client_id": app.config['META_APP_ID'],
        "client_secret": app.config['META_APP_SECRET'],
        "redirect_uri": app.config['META_REDIRECT_URI'],
        "code": code
    }

    print(f"Token exchange params: {params}")  # Debug log
    token_resp = requests.get(token_url, params=params)
    print(f"Token response status: {token_resp.status_code}")  # Debug log
    print(f"Token response text: {token_resp.text}")  # Debug log
    
    if token_resp.status_code != 200:
        flash(f"Failed to fetch access token: {token_resp.status_code} - {token_resp.text}", "danger")
        return redirect(url_for('main.dashboard'))

    access_token = token_resp.json().get("access_token")
    if not access_token:
        flash("No access token received from Meta", "danger")
        return redirect(url_for('main.dashboard'))

    # Get WABA info
    # business_info_url = f"https://graph.facebook.com/v19.0/me"
    # business_info = requests.get(business_info_url, params={"access_token": access_token}).json()
    # print(f"Business info: {business_info}")  # Debug log

    # Get WABA ID
    user = User.query.get(user_id)
    if not user:
        flash("User not found", "danger")
        return redirect(url_for('main.dashboard'))
        
    user.whatsapp_access_token = access_token


    # Get Business ID → from token's "me" response
    # business_id = business_info.get("id")
    # if business_id:
    #     # First get business accounts
    #     accounts_url = f"https://graph.facebook.com/v19.0/me/accounts"
    #     accounts_resp = requests.get(accounts_url, params={"access_token": access_token}).json()
    #     print(f"Accounts response: {accounts_resp}")  # Debug log
        
    #     # Look for WABA in business accounts
    #     waba_found = False
    #     for account in accounts_resp.get("data", []):
    #         account_id = account.get("id")
    #         if account_id:
    #             # Check if this account has WABA
    #             waba_list_url = f"https://graph.facebook.com/v19.0/{account_id}/owned_whatsapp_business_accounts"
    #             waba_resp = requests.get(waba_list_url, params={"access_token": access_token}).json()
    #             print(f"WABA response for account {account_id}: {waba_resp}")  # Debug log
                
    #             if "data" in waba_resp and waba_resp["data"]:
    #                 user.waba_id = waba_resp["data"][0]["id"]
    #                 waba_found = True
                    
    #                 # Now fetch phone numbers
    #                 phone_url = f"https://graph.facebook.com/v19.0/{user.waba_id}/phone_numbers"
    #                 phone_resp = requests.get(phone_url, params={"access_token": access_token}).json()
    #                 print(f"Phone response: {phone_resp}")  # Debug log
    #                 phones = phone_resp.get("data", [])
    #                 if phones:
    #                     user.phone_number_id = phones[0]["id"]
    #                 else:
    #                     print("No phone numbers found for WABA")
    #                 break
        
    #     if not waba_found:
    #         print("No WABA found in any business account")
    # else:
    #     print("No business ID found in response")

    # db.session.commit()
    
    # Check if we got WABA and phone number

    # For test setup: fetch WABA directly from app
    test_waba_id = "722746990372487"
    user.waba_id = test_waba_id

    # accounts_url = f"https://graph.facebook.com/v19.0/me/accounts"
    # accounts_resp = requests.get(accounts_url, params={"access_token": access_token}).json()
    # print(f"Accounts response: {accounts_resp}")


    app_waba_url = f"https://graph.facebook.com/v19.0/{test_waba_id}/phone_numbers"
    app_waba_resp = requests.get(app_waba_url, params={"access_token": access_token}).json()
    print(f"WABA linked to app: {app_waba_resp}")

    # The rest of the onboarding status logic remains the same
    waba_phones = app_waba_resp.get("data", [])
    if waba_phones:
        user.waba_id = test_waba_id  # Don't override with phone ID
        user.phone_number_id = waba_phones[0].get("id")  # Correctly assign the phone number ID

    if user.waba_id and user.phone_number_id:
        user.onboarding_status = 'Verified'
        flash("WhatsApp credentials saved successfully! You can now send messages.", "success")
    else:
        user.onboarding_status = 'In Progress'
        flash("WhatsApp setup in progress. You may need to create a WhatsApp Business Account or add a phone number in Meta Business Manager.", "warning")
    db.session.commit()
    return redirect(url_for('main.dashboard'))

@main.route('/business-verification', methods=['GET', 'POST'])
@login_required
def business_verification():
    form = UploadForm()
    if form.validate_on_submit():
        for file, filetype in [(form.pan_file.data, 'PAN'), (form.gst_file.data, 'GST')]:
            if file:
                filename = secure_filename(file.filename)
                filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
                file.save(filepath)
                upload = Upload(filename=filename, filetype=filetype, user_id=current_user.id)
                db.session.add(upload)
        db.session.commit()
        flash('Documents uploaded successfully!', 'success')
        return redirect(url_for('main.dashboard'))
    
    uploads = Upload.query.filter_by(user_id=current_user.id).all()
    return render_template('business_verification.html', form=form, uploads=uploads)

@main.route('/send-messages', methods=['GET', 'POST'])
@login_required
def send_messages():
    if current_user.onboarding_status != 'Verified':
        flash('Please complete WhatsApp setup first.', 'warning')
        return redirect(url_for('main.dashboard'))
    
    approved_templates = Template.query.filter_by(user_id=current_user.id, status='Approved').all()
    if not approved_templates:
        flash('No approved templates found. Please create templates first.', 'warning')
        return redirect(url_for('main.manage_templates'))
    
    msg_form = WhatsAppMessageForm()
    msg_form.template.choices = [(t.name, f"{t.name} ({t.language})") for t in approved_templates]
    
    if msg_form.validate_on_submit():
        recipient = msg_form.recipient.data
        template_name = msg_form.template.data
        lang = None
        template_obj = None
        
        # Find the template object
        for t in approved_templates:
            if t.name == template_name:
                lang = t.language
                template_obj = t
                break
        
        if not lang or not template_obj:
            flash("Invalid template selected.", "danger")
            return redirect(url_for('main.send_messages'))
        
        token = current_user.whatsapp_access_token
        phone_id = current_user.phone_number_id
        
        print(f"🔍 DEBUG - User ID: {current_user.id}")
        print(f"🔍 DEBUG - Phone ID: {phone_id}")
        print(f"🔍 DEBUG - Token (first 20 chars): {token[:20] if token else 'None'}...")
        print(f"🔍 DEBUG - Token length: {len(token) if token else 0}")
        print(f"🔍 DEBUG - Recipient: {recipient}")
        print(f"🔍 DEBUG - Template: {template_name}")
        print(f"🔍 DEBUG - Language: {lang}")
        
        if not token or not phone_id:
            print("❌ DEBUG - Missing credentials!")
            flash("Missing WhatsApp credentials", "danger")
            return redirect(url_for('main.dashboard'))
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        url = f'https://graph.facebook.com/v19.0/{phone_id}/messages'
        payload = {
            "messaging_product": "whatsapp",
            "to": recipient,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": lang}
            }
        }
        
        print(f"🔍 DEBUG - URL: {url}")
        print(f"🔍 DEBUG - Headers: {headers}")
        print(f"🔍 DEBUG - Payload: {payload}")
        
        print("📤 DEBUG - Sending request to WhatsApp API...")
        response = requests.post(url, headers=headers, json=payload)
        
        print(f"📥 DEBUG - Response Status: {response.status_code}")
        print(f"📥 DEBUG - Response Headers: {dict(response.headers)}")
        print(f"📥 DEBUG - Response Text: {response.text}")
        
        meta_message_id = None
        if response.status_code == 200:
            resp_json = response.json()
            if 'messages' in resp_json and resp_json['messages']:
                meta_message_id = resp_json['messages'][0].get('id')
            flash("Message sent successfully!", "success")
        else:
            flash(f"Failed to send message: {response.status_code} — {response.text}", "danger")
        
        # Save message history
        history = MessageHistory(
            user_id=current_user.id,
            recipient=recipient,
            template_id=template_obj.id,
            meta_message_id=meta_message_id,
            status='sent'
        )
        db.session.add(history)
        db.session.commit()
        
        return redirect(url_for('main.send_messages'))
    
    # Get recent messages for display
    recent_messages = MessageHistory.query.filter_by(user_id=current_user.id).order_by(MessageHistory.created_at.desc()).limit(5).all()
    
    return render_template('send_messages.html', form=msg_form, templates=approved_templates, recent_messages=recent_messages)

@main.route('/message-history')
@login_required
def message_history():
    if current_user.onboarding_status != 'Verified':
        flash('Please complete WhatsApp setup first.', 'warning')
        return redirect(url_for('main.dashboard'))
    
    page = request.args.get('page', 1, type=int)
    messages = MessageHistory.query.filter_by(user_id=current_user.id).order_by(MessageHistory.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('message_history.html', messages=messages)

@main.route('/template-library')
@login_required
def template_library():
    category = request.args.get('category', 'all')
    
    # Get all categories for filter
    from app.models import TemplateLibrary
    categories = db.session.query(TemplateLibrary.category).distinct().all()
    categories = [cat[0] for cat in categories]
    
    # Filter templates by category
    if category == 'all':
        templates = TemplateLibrary.query.filter_by(is_active=True).all()
    else:
        templates = TemplateLibrary.query.filter_by(category=category, is_active=True).all()
    
    return render_template('template_library.html', templates=templates, categories=categories, selected_category=category)

@main.route('/use-template/<int:template_id>')
@login_required
def use_template(template_id):
    from app.models import TemplateLibrary
    library_template = TemplateLibrary.query.get_or_404(template_id)
    
    # Create a new template for the user based on the library template
    new_template = Template(
        user_id=current_user.id,
        name=f"{library_template.name}_{current_user.id}",
        language=library_template.language,
        content=library_template.content,
        header_type=library_template.header_type,
        header_text=library_template.header_text,
        footer_text=library_template.footer_text,
        status='Pending'
    )
    
    # If user has WhatsApp connected, submit to Meta
    if current_user.whatsapp_access_token and current_user.waba_id:
        try:
            # Build components for Meta API
            components = []
            
            # Header
            if library_template.header_type == 'TEXT' and library_template.header_text:
                components.append({"type": "HEADER", "format": "TEXT", "text": library_template.header_text})
            
            # Body (always required)
            components.append({"type": "BODY", "text": library_template.content})
            
            # Footer
            if library_template.footer_text:
                components.append({"type": "FOOTER", "text": library_template.footer_text})
            
            # Submit to Meta
            url = f"https://graph.facebook.com/v19.0/{current_user.waba_id}/message_templates"
            headers = {"Authorization": f"Bearer {current_user.whatsapp_access_token}"}
            payload = {
                "name": new_template.name,
                "language": {"code": new_template.language},
                "components": components,
                "category": "TRANSACTIONAL"
            }
            
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                resp_json = response.json()
                new_template.meta_template_id = resp_json.get("id")
                flash(f'Template "{library_template.name}" added and submitted for approval!', 'success')
            else:
                flash(f"Template added but Meta submission failed: {response.text}", 'warning')
        except Exception as e:
            flash(f"Template added but Meta submission failed: {e}", 'warning')
    else:
        flash(f'Template "{library_template.name}" added! Complete WhatsApp setup to use it.', 'info')
    
    db.session.add(new_template)
    db.session.commit()
    
    return redirect(url_for('main.manage_templates'))

@main.route('/bulk-messages', methods=['GET', 'POST'])
@login_required
def bulk_messages():
    if current_user.onboarding_status != 'Verified':
        flash('Please complete WhatsApp setup first.', 'warning')
        return redirect(url_for('main.dashboard'))
    
    approved_templates = Template.query.filter_by(user_id=current_user.id, status='Approved').all()
    if not approved_templates:
        flash('No approved templates found. Please create templates first.', 'warning')
        return redirect(url_for('main.template_library'))
    
    from app.forms import BulkMessageForm
    form = BulkMessageForm()
    form.template.choices = [(t.name, f"{t.name} ({t.language})") for t in approved_templates]
    
    if form.validate_on_submit():
        # Get recipients from text area or CSV file
        recipients = []
        
        if form.csv_file.data:
            # Handle CSV upload
            import csv
            import io
            csv_file = form.csv_file.data
            csv_content = csv_file.read().decode('utf-8')
            csv_reader = csv.reader(io.StringIO(csv_content))
            
            for row in csv_reader:
                if row and len(row) > 0:  # Skip empty rows
                    phone = row[0].strip()
                    if phone and phone.isdigit() and len(phone) >= 10:
                        recipients.append(phone)
        else:
            # Handle text area input
            recipients_text = form.recipients_text.data.strip()
            if recipients_text:
                for line in recipients_text.split('\n'):
                    phone = line.strip()
                    if phone and phone.isdigit() and len(phone) >= 10:
                        recipients.append(phone)
        
        if not recipients:
            flash('No valid phone numbers found. Please check your input.', 'danger')
            return redirect(url_for('main.bulk_messages'))
        
        # Check message limits
        remaining_messages = current_user.get_remaining_messages()
        if len(recipients) > remaining_messages:
            flash(f'You can only send {remaining_messages} more messages this month. You tried to send {len(recipients)} messages.', 'warning')
            return redirect(url_for('main.bulk_messages'))
        
        # Find the selected template
        template_name = form.template.data
        template_obj = None
        for t in approved_templates:
            if t.name == template_name:
                template_obj = t
                break
        
        if not template_obj:
            flash("Invalid template selected.", "danger")
            return redirect(url_for('main.bulk_messages'))
        
        # Send messages
        success_count = 0
        failed_count = 0
        
        token = current_user.whatsapp_access_token
        phone_id = current_user.phone_number_id
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        url = f'https://graph.facebook.com/v19.0/{phone_id}/messages'
        
        for recipient in recipients:
            payload = {
                "messaging_product": "whatsapp",
                "to": recipient,
                "type": "template",
                "template": {
                    "name": template_name,
                    "language": {"code": template_obj.language}
                }
            }
            
            try:
                response = requests.post(url, headers=headers, json=payload)
                meta_message_id = None
                
                if response.status_code == 200:
                    resp_json = response.json()
                    if 'messages' in resp_json and resp_json['messages']:
                        meta_message_id = resp_json['messages'][0].get('id')
                    success_count += 1
                else:
                    failed_count += 1
                
                # Save message history
                history = MessageHistory(
                    user_id=current_user.id,
                    recipient=recipient,
                    template_id=template_obj.id,
                    meta_message_id=meta_message_id,
                    status='sent' if response.status_code == 200 else 'failed'
                )
                db.session.add(history)
                
            except Exception as e:
                failed_count += 1
                # Save failed message history
                history = MessageHistory(
                    user_id=current_user.id,
                    recipient=recipient,
                    template_id=template_obj.id,
                    status='failed'
                )
                db.session.add(history)
        
        # Update user's message count
        current_user.messages_sent_this_month += success_count
        db.session.commit()
        
        if success_count > 0:
            flash(f'Successfully sent {success_count} messages!', 'success')
        if failed_count > 0:
            flash(f'{failed_count} messages failed to send.', 'warning')
        
        return redirect(url_for('main.message_history'))
    
    return render_template('bulk_messages.html', form=form, templates=approved_templates, 
                         remaining_messages=current_user.get_remaining_messages())

@main.route('/schedule-messages', methods=['GET', 'POST'])
@login_required
def schedule_messages():
    if current_user.onboarding_status != 'Verified':
        flash('Please complete WhatsApp setup first.', 'warning')
        return redirect(url_for('main.dashboard'))
    
    approved_templates = Template.query.filter_by(user_id=current_user.id, status='Approved').all()
    if not approved_templates:
        flash('No approved templates found. Please create templates first.', 'warning')
        return redirect(url_for('main.template_library'))
    
    from app.forms import ScheduleMessageForm
    form = ScheduleMessageForm()
    form.template.choices = [(t.name, f"{t.name} ({t.language})") for t in approved_templates]
    
    if form.validate_on_submit():
        from datetime import datetime
        from app.models import ScheduledMessage
        
        # Combine date and time
        try:
            scheduled_datetime = datetime.strptime(
                f"{form.scheduled_date.data} {form.scheduled_time.data}", 
                "%Y-%m-%d %H:%M"
            )
            
            # Check if the scheduled time is in the future
            if scheduled_datetime <= datetime.now():
                flash('Scheduled time must be in the future.', 'danger')
                return redirect(url_for('main.schedule_messages'))
            
        except ValueError:
            flash('Invalid date or time format.', 'danger')
            return redirect(url_for('main.schedule_messages'))
        
        # Find the selected template
        template_name = form.template.data
        template_obj = None
        for t in approved_templates:
            if t.name == template_name:
                template_obj = t
                break
        
        if not template_obj:
            flash("Invalid template selected.", "danger")
            return redirect(url_for('main.schedule_messages'))
        
        # Create scheduled message
        scheduled_msg = ScheduledMessage(
            user_id=current_user.id,
            recipient=form.recipient.data,
            template_id=template_obj.id,
            scheduled_time=scheduled_datetime,
            status='pending'
        )
        
        db.session.add(scheduled_msg)
        db.session.commit()
        
        flash(f'Message scheduled for {scheduled_datetime.strftime("%B %d, %Y at %I:%M %p")}!', 'success')
        return redirect(url_for('main.scheduled_messages'))
    
    return render_template('schedule_messages.html', form=form, templates=approved_templates)

@main.route('/scheduled-messages')
@login_required
def scheduled_messages():
    if current_user.onboarding_status != 'Verified':
        flash('Please complete WhatsApp setup first.', 'warning')
        return redirect(url_for('main.dashboard'))
    
    from app.models import ScheduledMessage
    page = request.args.get('page', 1, type=int)
    
    scheduled = ScheduledMessage.query.filter_by(user_id=current_user.id).order_by(
        ScheduledMessage.scheduled_time.desc()
    ).paginate(page=page, per_page=20, error_out=False)
    
    return render_template('scheduled_messages.html', scheduled=scheduled)

@main.route('/cancel-scheduled/<int:message_id>')
@login_required
def cancel_scheduled(message_id):
    from app.models import ScheduledMessage
    scheduled_msg = ScheduledMessage.query.filter_by(
        id=message_id, 
        user_id=current_user.id, 
        status='pending'
    ).first_or_404()
    
    scheduled_msg.status = 'cancelled'
    db.session.commit()
    
    flash('Scheduled message cancelled successfully.', 'success')
    return redirect(url_for('main.scheduled_messages'))

@main.route('/analytics')
@login_required
def analytics():
    if current_user.onboarding_status != 'Verified':
        flash('Please complete WhatsApp setup first.', 'warning')
        return redirect(url_for('main.dashboard'))
    
    from datetime import datetime, timedelta
    from sqlalchemy import func, and_
    
    # Date range for analytics (last 30 days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    # Basic stats
    total_messages = MessageHistory.query.filter_by(user_id=current_user.id).count()
    messages_this_month = MessageHistory.query.filter(
        and_(
            MessageHistory.user_id == current_user.id,
            MessageHistory.created_at >= start_date
        )
    ).count()
    
    # Status breakdown
    status_stats = db.session.query(
        MessageHistory.status,
        func.count(MessageHistory.id).label('count')
    ).filter_by(user_id=current_user.id).group_by(MessageHistory.status).all()
    
    # Daily message counts (last 7 days)
    daily_stats = []
    for i in range(7):
        day = end_date - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        
        count = MessageHistory.query.filter(
            and_(
                MessageHistory.user_id == current_user.id,
                MessageHistory.created_at >= day_start,
                MessageHistory.created_at < day_end
            )
        ).count()
        
        daily_stats.append({
            'date': day.strftime('%Y-%m-%d'),
            'day': day.strftime('%a'),
            'count': count
        })
    
    daily_stats.reverse()  # Show oldest to newest
    
    # Template usage stats
    template_stats = db.session.query(
        Template.name,
        func.count(MessageHistory.id).label('usage_count')
    ).join(MessageHistory, Template.id == MessageHistory.template_id)\
     .filter(MessageHistory.user_id == current_user.id)\
     .group_by(Template.name)\
     .order_by(func.count(MessageHistory.id).desc())\
     .limit(5).all()
    
    # Calculate delivery rate
    delivered_count = MessageHistory.query.filter_by(
        user_id=current_user.id, 
        status='delivered'
    ).count()
    delivery_rate = (delivered_count / total_messages * 100) if total_messages > 0 else 0
    
    # Calculate read rate
    read_count = MessageHistory.query.filter_by(
        user_id=current_user.id, 
        status='read'
    ).count()
    read_rate = (read_count / total_messages * 100) if total_messages > 0 else 0
    
    return render_template('analytics.html',
                         total_messages=total_messages,
                         messages_this_month=messages_this_month,
                         status_stats=status_stats,
                         daily_stats=daily_stats,
                         template_stats=template_stats,
                         delivery_rate=delivery_rate,
                         read_rate=read_rate,
                         remaining_messages=current_user.get_remaining_messages())

@main.route('/pricing')
def pricing():
    from app.models import SubscriptionPlan
    plans = SubscriptionPlan.query.filter_by(is_active=True).order_by(SubscriptionPlan.price).all()
    return render_template('pricing.html', plans=plans)

@main.route('/subscription')
@login_required
def subscription():
    from app.models import SubscriptionPlan
    current_plan = current_user.get_current_plan()
    available_plans = SubscriptionPlan.query.filter_by(is_active=True).order_by(SubscriptionPlan.price).all()
    
    return render_template('subscription.html', 
                         current_plan=current_plan, 
                         available_plans=available_plans,
                         subscription=current_user.subscription)

@main.route('/upgrade/<int:plan_id>')
@login_required
def upgrade_plan(plan_id):
    from app.models import SubscriptionPlan
    
    plan = SubscriptionPlan.query.get_or_404(plan_id)
    
    # Check if user already has this plan
    current_plan = current_user.get_current_plan()
    if current_plan and current_plan.id == plan_id:
        flash('You already have this plan!', 'info')
        return redirect(url_for('main.subscription'))
    
    # For free plan, upgrade immediately
    if plan.price == 0:
        return activate_free_plan(plan)
    
    # For paid plans, redirect to payment
    return redirect(url_for('main.create_payment', plan_id=plan.id))

def activate_free_plan(plan):
    """Activate free plan immediately without payment"""
    from app.models import UserSubscription
    from datetime import datetime, timedelta
    
    # Cancel existing subscription if any
    if current_user.subscription:
        current_user.subscription.status = 'cancelled'
    
    # Create new subscription
    end_date = datetime.now() + timedelta(days=365)  # Free plan for 1 year
    new_subscription = UserSubscription(
        user_id=current_user.id,
        plan_id=plan.id,
        status='active',
        end_date=end_date,
        auto_renew=True
    )
    
    db.session.add(new_subscription)
    db.session.flush()
    
    # Update user's subscription and message limit
    current_user.subscription_id = new_subscription.id
    current_user.message_limit = plan.message_limit
    current_user.messages_sent_this_month = 0
    
    db.session.commit()
    
    flash(f'Successfully activated {plan.name} plan!', 'success')
    return redirect(url_for('main.subscription'))

@main.route('/create-payment/<int:plan_id>')
@login_required
def create_payment(plan_id):
    from app.models import SubscriptionPlan, Payment
    import razorpay
    
    plan = SubscriptionPlan.query.get_or_404(plan_id)
    
    # Initialize Razorpay client
    client = razorpay.Client(auth=(app.config['RAZORPAY_KEY_ID'], app.config['RAZORPAY_KEY_SECRET']))
    
    # Create Razorpay order
    amount = int(plan.price * 100)  # Convert to paise
    order_data = {
        'amount': amount,
        'currency': 'INR',
        'receipt': f'order_{current_user.id}_{plan.id}_{int(datetime.now().timestamp())}',
        'notes': {
            'user_id': current_user.id,
            'plan_id': plan.id,
            'plan_name': plan.name
        }
    }
    
    try:
        razorpay_order = client.order.create(data=order_data)
        
        # Create payment record
        payment = Payment(
            user_id=current_user.id,
            plan_id=plan.id,
            razorpay_order_id=razorpay_order['id'],
            amount=plan.price,
            status='pending'
        )
        db.session.add(payment)
        db.session.commit()
        
        return render_template('payment.html', 
                             order=razorpay_order, 
                             plan=plan, 
                             payment=payment,
                             razorpay_key=app.config['RAZORPAY_KEY_ID'])
        
    except Exception as e:
        flash(f'Error creating payment: {str(e)}', 'danger')
        return redirect(url_for('main.subscription'))

@main.route('/payment-success', methods=['POST'])
@login_required
def payment_success():
    from app.models import Payment, UserSubscription
    import razorpay
    from datetime import datetime, timedelta
    
    # Get payment details from form
    razorpay_order_id = request.form.get('razorpay_order_id')
    razorpay_payment_id = request.form.get('razorpay_payment_id')
    razorpay_signature = request.form.get('razorpay_signature')
    
    # Find the payment record
    payment = Payment.query.filter_by(
        razorpay_order_id=razorpay_order_id,
        user_id=current_user.id
    ).first()
    
    if not payment:
        flash('Payment record not found!', 'danger')
        return redirect(url_for('main.subscription'))
    
    # Initialize Razorpay client
    client = razorpay.Client(auth=(app.config['RAZORPAY_KEY_ID'], app.config['RAZORPAY_KEY_SECRET']))
    
    try:
        # Verify payment signature
        client.utility.verify_payment_signature({
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        })
        
        # Update payment record
        payment.razorpay_payment_id = razorpay_payment_id
        payment.razorpay_signature = razorpay_signature
        payment.status = 'completed'
        payment.updated_at = datetime.now()
        
        # Cancel existing subscription if any
        if current_user.subscription:
            current_user.subscription.status = 'cancelled'
        
        # Create new subscription
        end_date = datetime.now() + timedelta(days=30)  # 30-day subscription
        new_subscription = UserSubscription(
            user_id=current_user.id,
            plan_id=payment.plan_id,
            payment_id=payment.id,
            status='active',
            end_date=end_date,
            auto_renew=True
        )
        
        db.session.add(new_subscription)
        db.session.flush()
        
        # Update user's subscription and message limit
        current_user.subscription_id = new_subscription.id
        current_user.message_limit = payment.plan.message_limit
        current_user.messages_sent_this_month = 0  # Reset for new plan
        
        db.session.commit()
        
        # Send confirmation email (we'll implement this next)
        send_subscription_confirmation_email(current_user, payment.plan)
        
        flash(f'Payment successful! Welcome to {payment.plan.name} plan!', 'success')
        return redirect(url_for('main.subscription'))
        
    except razorpay.errors.SignatureVerificationError:
        payment.status = 'failed'
        db.session.commit()
        flash('Payment verification failed!', 'danger')
        return redirect(url_for('main.subscription'))
    except Exception as e:
        payment.status = 'failed'
        db.session.commit()
        flash(f'Payment processing error: {str(e)}', 'danger')
        return redirect(url_for('main.subscription'))

@main.route('/payment-failed')
@login_required
def payment_failed():
    flash('Payment was cancelled or failed. Please try again.', 'warning')
    return redirect(url_for('main.subscription'))

def send_subscription_confirmation_email(user, plan):
    """Send subscription confirmation email"""
    # We'll implement email functionality next
    pass

@main.route('/cancel-subscription')
@login_required
def cancel_subscription():
    if current_user.subscription and current_user.subscription.status == 'active':
        current_user.subscription.status = 'cancelled'
        current_user.subscription.auto_renew = False
        
        # Revert to free plan limits
        current_user.message_limit = 100
        
        db.session.commit()
        flash('Your subscription has been cancelled. You will continue to have access until the end of your billing period.', 'info')
    else:
        flash('No active subscription found.', 'warning')
    
    return redirect(url_for('main.subscription'))

@main.route('/webhook/meta', methods=['POST'])
def meta_webhook():
    data = request.json
    # Handle template status updates
    if data and 'entry' in data:
        for entry in data['entry']:
            for change in entry.get('changes', []):
                value = change.get('value', {})
                # Template status update
                if 'message_template_id' in value and 'event' in value:
                    meta_template_id = value['message_template_id']
                    event = value['event']  # APPROVED, REJECTED, etc.
                    template = Template.query.filter_by(meta_template_id=meta_template_id).first()
                    if template:
                        if event == 'APPROVED':
                            template.status = 'Approved'
                        elif event == 'REJECTED':
                            template.status = 'Rejected'
                        db.session.commit()
                # Message DLR (delivery status)
                if 'statuses' in value:
                    for status in value['statuses']:
                        meta_message_id = status.get('id')
                        status_str = status.get('status')  # delivered, read, failed, etc.
                        if meta_message_id and status_str:
                            history = MessageHistory.query.filter_by(meta_message_id=meta_message_id).first()
                            if history:
                                history.status = status_str
                                db.session.commit()
    return '', 200

def assign_dedicated_whatsapp_number(user_id, business_name):
    """Assign a dedicated WhatsApp number to each business"""
    
    # Pool of WhatsApp numbers you own (you need to buy/register these)
    available_numbers = [
        {'phone_id': 'phone_id_1', 'number': '+919999111111', 'display_name': 'Business Line 1'},
        {'phone_id': 'phone_id_2', 'number': '+919999222222', 'display_name': 'Business Line 2'},
        {'phone_id': 'phone_id_3', 'number': '+919999333333', 'display_name': 'Business Line 3'},
        {'phone_id': 'phone_id_4', 'number': '+919999444444', 'display_name': 'Business Line 4'},
        # Add more numbers as you scale
    ]
    
    # Simple assignment: use user_id to assign numbers in round-robin
    assigned_number = available_numbers[user_id % len(available_numbers)]
    
    # In production, you would:
    # 1. Update WhatsApp Business Profile for this number with business_name
    # 2. Set business description, category, etc.
    # 3. Track assignments in a separate table
    
    return assigned_number['phone_id']

def auto_create_starter_templates(user_id):
    """Automatically create basic templates for new users"""
    from app.models import TemplateLibrary
    
    # Get 3 most popular templates from library
    popular_templates = TemplateLibrary.query.filter_by(is_active=True).limit(3).all()
    
    for lib_template in popular_templates:
        # Create approved template for user (skip Meta approval for demo)
        user_template = Template(
            user_id=user_id,
            name=f"{lib_template.name.replace(' ', '_').lower()}_{user_id}",
            language='en_US',
            content=lib_template.content,
            status='Approved',  # Auto-approve for demo
            header_type=lib_template.header_type,
            header_text=lib_template.header_text,
            footer_text=lib_template.footer_text
        )
        db.session.add(user_template)