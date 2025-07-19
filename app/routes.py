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
            flash('User already exists.', 'danger')
            return redirect(url_for('main.register'))
        hashed_pw = generate_password_hash(form.password.data)
        user = User(email=form.email.data, password=hashed_pw)
        db.session.add(user)
        db.session.commit()
        flash('Registered! Please log in.', 'success')
        return redirect(url_for('main.login'))
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

@main.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    form = UploadForm()
    # Only show approved templates for sending
    approved_templates = Template.query.filter_by(user_id=current_user.id, status='Approved').all()
    msg_form = WhatsAppMessageForm()
    msg_form.template.choices = [(t.name, f"{t.name} ({t.language})") for t in approved_templates]
    if form.validate_on_submit():
        for file, filetype in [(form.pan_file.data, 'PAN'), (form.gst_file.data, 'GST')]:
            if file:
                filename = secure_filename(file.filename)
                filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
                file.save(filepath)
                upload = Upload(filename=filename, filetype=filetype, user_id=current_user.id)
                db.session.add(upload)
        db.session.commit()
        flash('Files uploaded successfully!', 'success')
        return redirect(url_for('main.dashboard'))
    uploads = Upload.query.filter_by(user_id=current_user.id).all()
    has_pan = any(u.filetype == 'PAN' for u in uploads)
    has_gst = any(u.filetype == 'GST' for u in uploads)
    docs_uploaded = has_pan and has_gst
    onboarding_status = current_user.onboarding_status
    can_onboard = docs_uploaded and onboarding_status != 'Verified'
    can_send = onboarding_status == 'Verified' and current_user.whatsapp_access_token and current_user.phone_number_id and approved_templates
    message_history = MessageHistory.query.filter_by(user_id=current_user.id).order_by(MessageHistory.created_at.desc()).all()
    return render_template('dashboard.html', form=form, uploads=uploads, msg_form=msg_form,
                           docs_uploaded=docs_uploaded, can_onboard=can_onboard, can_send=can_send,
                           onboarding_status=onboarding_status, approved_templates=approved_templates,
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

@main.route('/send-message', methods=['POST'])
@login_required
def send_message():
    # Only allow sending with approved templates
    approved_templates = Template.query.filter_by(user_id=current_user.id, status='Approved').all()
    msg_form = WhatsAppMessageForm()
    msg_form.template.choices = [(t.name, f"{t.name} ({t.language})") for t in approved_templates]
    if msg_form.validate_on_submit():
        recipient = msg_form.recipient.data
        template_name = msg_form.template.data
        lang = None
        template_obj = None
        # Find the language and template object for the selected template
        for t in approved_templates:
            if t.name == template_name:
                lang = t.language
                template_obj = t
                break
        if not lang or not template_obj:
            flash("Invalid template selected.", "danger")
            return redirect(url_for('main.dashboard'))
        token = current_user.whatsapp_access_token
        phone_id = current_user.phone_number_id
        if not token or not phone_id:
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
        response = requests.post(url, headers=headers, json=payload)
        meta_message_id = None
        if response.status_code == 200:
            resp_json = response.json()
            # Meta returns message ID in 'messages' list
            if 'messages' in resp_json and resp_json['messages']:
                meta_message_id = resp_json['messages'][0].get('id')
            flash("Message sent successfully!", "success")
        else:
            flash(f"Failed: {response.status_code} — {response.text}", "danger")
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
    return redirect(url_for('main.dashboard'))

@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))

@main.route('/onboard/start')
@login_required
def start_onboarding():
    base_url = 'https://www.facebook.com/dialog/oauth?'
    query = {
        'client_id': app.config['META_APP_ID'],
        'redirect_uri': app.config['META_REDIRECT_URI'],
        'state': current_user.id,  # track user session
        'scope': app.config['META_PERMISSIONS']
    }
    signup_url = base_url + urllib.parse.urlencode(query)
    return redirect(signup_url)

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
