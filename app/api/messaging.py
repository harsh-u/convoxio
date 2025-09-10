import logging
import requests
import csv
import io
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.models import Template, MessageHistory, Contact, ScheduledMessage
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

messaging_api = Blueprint('messaging_api', __name__)

@messaging_api.route('/send-message', methods=['POST'])
@login_required
def send_message():
    """Send individual WhatsApp message"""
    try:
        if current_user.onboarding_status != 'Verified':
            return jsonify({'error': 'WhatsApp onboarding not completed'}), 400
        
        if not current_user.can_send_message():
            return jsonify({'error': 'Monthly message limit reached'}), 400
        
        data = request.get_json()
        
        # Validate required fields
        if not data.get('recipient') or not data.get('template_id'):
            return jsonify({'error': 'Recipient and template_id are required'}), 400
        
        # Get template
        template = Template.query.filter_by(
            id=data['template_id'], 
            user_id=current_user.id,
            status='Approved'
        ).first()
        
        if not template:
            return jsonify({'error': 'Template not found or not approved'}), 404
        
        recipient = data['recipient']
        recipient_name = data.get('recipient_name', recipient)
        
        logger.info(f"📤 Sending message to {recipient} using template {template.name}")
        
        # Prepare WhatsApp API request
        message_data = {
            'messaging_product': 'whatsapp',
            'to': recipient,
            'type': 'template',
            'template': {
                'name': template.name,
                'language': {
                    'code': template.language
                }
            }
        }
        
        url = f"https://graph.facebook.com/v19.0/{current_user.phone_number_id}/messages"
        headers = {
            'Authorization': f'Bearer {current_user.whatsapp_access_token}',
            'Content-Type': 'application/json'
        }
        
        # Send message
        response = requests.post(url, json=message_data, headers=headers)
        
        meta_message_id = None
        status = 'failed'
        
        if response.status_code == 200:
            result = response.json()
            meta_message_id = result.get('messages', [{}])[0].get('id')
            status = 'sent'
            
            # Update user's message count
            current_user.messages_sent_this_month += 1
            
            logger.info(f"✅ Message sent successfully to {recipient}")
        else:
            logger.error(f"❌ WhatsApp API error: {response.status_code} - {response.text}")
        
        # Save message history
        message = MessageHistory(
            user_id=current_user.id,
            recipient=recipient,
            recipient_name=recipient_name,
            template_id=template.id,
            message_content=template.content,
            message_type='template',
            meta_message_id=meta_message_id,
            status=status
        )
        db.session.add(message)
        
        # Create or update contact
        contact = Contact.query.filter_by(
            user_id=current_user.id,
            phone_number=recipient
        ).first()
        
        if not contact:
            contact = Contact(
                user_id=current_user.id,
                phone_number=recipient,
                name=recipient_name,
                last_message_at=message.created_at
            )
            db.session.add(contact)
        else:
            contact.last_message_at = message.created_at
            if recipient_name and recipient_name != recipient:
                contact.name = recipient_name
        
        db.session.commit()
        
        if response.status_code == 200:
            return jsonify({
                'success': True,
                'message': 'Message sent successfully',
                'message_id': message.id,
                'meta_message_id': meta_message_id,
                'remaining_messages': current_user.get_remaining_messages()
            }), 200
        else:
            error_response = response.json() if response.headers.get('content-type') == 'application/json' else {'error': response.text}
            return jsonify({
                'success': False,
                'error': f"Failed to send message: {error_response}",
                'message_id': message.id
            }), 400
            
    except Exception as e:
        logger.error(f"❌ Send message error: {str(e)}")
        return jsonify({'error': 'Failed to send message'}), 500

@messaging_api.route('/send-bulk', methods=['POST'])
@login_required
def send_bulk_messages():
    """Send bulk WhatsApp messages"""
    try:
        if current_user.onboarding_status != 'Verified':
            return jsonify({'error': 'WhatsApp onboarding not completed'}), 400
        
        data = request.get_json()
        
        # Validate required fields
        if not data.get('template_id'):
            return jsonify({'error': 'template_id is required'}), 400
        
        # Get template
        template = Template.query.filter_by(
            id=data['template_id'], 
            user_id=current_user.id,
            status='Approved'
        ).first()
        
        if not template:
            return jsonify({'error': 'Template not found or not approved'}), 404
        
        # Get recipients list
        recipients = []
        if data.get('recipients_text'):
            # Parse text input (one number per line)
            recipients = [line.strip() for line in data['recipients_text'].split('\n') if line.strip()]
        elif data.get('recipients_list'):
            # Direct list of recipients
            recipients = data['recipients_list']
        
        if not recipients:
            return jsonify({'error': 'No recipients provided'}), 400
        
        # Check message limit
        if current_user.messages_sent_this_month + len(recipients) > current_user.message_limit:
            return jsonify({
                'error': f'Bulk send would exceed monthly limit. You can send {current_user.get_remaining_messages()} more messages.'
            }), 400
        
        logger.info(f"📤 Sending bulk messages to {len(recipients)} recipients using template {template.name}")
        
        sent_count = 0
        failed_count = 0
        results = []
        
        for recipient in recipients:
            try:
                # Prepare WhatsApp API request
                message_data = {
                    'messaging_product': 'whatsapp',
                    'to': recipient,
                    'type': 'template',
                    'template': {
                        'name': template.name,
                        'language': {
                            'code': template.language
                        }
                    }
                }
                
                url = f"https://graph.facebook.com/v19.0/{current_user.phone_number_id}/messages"
                headers = {
                    'Authorization': f'Bearer {current_user.whatsapp_access_token}',
                    'Content-Type': 'application/json'
                }
                
                # Send message
                response = requests.post(url, json=message_data, headers=headers)
                
                meta_message_id = None
                status = 'failed'
                
                if response.status_code == 200:
                    result = response.json()
                    meta_message_id = result.get('messages', [{}])[0].get('id')
                    status = 'sent'
                    sent_count += 1
                    current_user.messages_sent_this_month += 1
                else:
                    failed_count += 1
                    logger.error(f"❌ Failed to send to {recipient}: {response.text}")
                
                # Save message history
                message = MessageHistory(
                    user_id=current_user.id,
                    recipient=recipient,
                    template_id=template.id,
                    message_content=template.content,
                    message_type='template',
                    meta_message_id=meta_message_id,
                    status=status
                )
                db.session.add(message)
                
                # Create or update contact
                contact = Contact.query.filter_by(
                    user_id=current_user.id,
                    phone_number=recipient
                ).first()
                
                if not contact:
                    contact = Contact(
                        user_id=current_user.id,
                        phone_number=recipient,
                        name=recipient,
                        last_message_at=message.created_at
                    )
                    db.session.add(contact)
                else:
                    contact.last_message_at = message.created_at
                
                results.append({
                    'recipient': recipient,
                    'status': status,
                    'message_id': message.id
                })
                
            except Exception as e:
                failed_count += 1
                logger.error(f"❌ Error sending to {recipient}: {str(e)}")
                results.append({
                    'recipient': recipient,
                    'status': 'failed',
                    'error': str(e)
                })
        
        db.session.commit()
        
        logger.info(f"✅ Bulk send completed: {sent_count} sent, {failed_count} failed")
        
        return jsonify({
            'success': True,
            'message': f'Bulk send completed: {sent_count} sent, {failed_count} failed',
            'sent_count': sent_count,
            'failed_count': failed_count,
            'remaining_messages': current_user.get_remaining_messages(),
            'results': results
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Bulk send error: {str(e)}")
        return jsonify({'error': 'Failed to send bulk messages'}), 500

@messaging_api.route('/schedule-message', methods=['POST'])
@login_required
def schedule_message():
    """Schedule a message for future delivery"""
    try:
        if current_user.onboarding_status != 'Verified':
            return jsonify({'error': 'WhatsApp onboarding not completed'}), 400
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['recipient', 'template_id', 'scheduled_datetime']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Get template
        template = Template.query.filter_by(
            id=data['template_id'], 
            user_id=current_user.id,
            status='Approved'
        ).first()
        
        if not template:
            return jsonify({'error': 'Template not found or not approved'}), 404
        
        # Parse scheduled datetime
        try:
            scheduled_time = datetime.fromisoformat(data['scheduled_datetime'].replace('Z', '+00:00'))
        except ValueError:
            return jsonify({'error': 'Invalid datetime format. Use ISO format.'}), 400
        
        # Check if scheduled time is in the future
        if scheduled_time <= datetime.now():
            return jsonify({'error': 'Scheduled time must be in the future'}), 400
        
        # Create scheduled message
        scheduled_msg = ScheduledMessage(
            user_id=current_user.id,
            recipient=data['recipient'],
            template_id=template.id,
            scheduled_time=scheduled_time,
            status='pending'
        )
        
        db.session.add(scheduled_msg)
        db.session.commit()
        
        logger.info(f"📅 Message scheduled for {scheduled_time} to {data['recipient']}")
        
        return jsonify({
            'success': True,
            'message': 'Message scheduled successfully',
            'scheduled_message_id': scheduled_msg.id,
            'scheduled_time': scheduled_time.isoformat()
        }), 201
        
    except Exception as e:
        logger.error(f"❌ Schedule message error: {str(e)}")
        return jsonify({'error': 'Failed to schedule message'}), 500

@messaging_api.route('/scheduled-messages', methods=['GET'])
@login_required
def get_scheduled_messages():
    """Get all scheduled messages for current user"""
    try:
        scheduled_messages = ScheduledMessage.query.filter_by(user_id=current_user.id)\
            .order_by(ScheduledMessage.scheduled_time.desc()).all()
        
        return jsonify({
            'success': True,
            'scheduled_messages': [{
                'id': msg.id,
                'recipient': msg.recipient,
                'template_id': msg.template_id,
                'template_name': msg.template.name if msg.template else None,
                'scheduled_time': msg.scheduled_time.isoformat(),
                'status': msg.status,
                'created_at': msg.created_at.isoformat(),
                'sent_at': msg.sent_at.isoformat() if msg.sent_at else None,
                'error_message': msg.error_message
            } for msg in scheduled_messages]
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Get scheduled messages error: {str(e)}")
        return jsonify({'error': 'Failed to load scheduled messages'}), 500

@messaging_api.route('/scheduled-messages/<int:msg_id>/cancel', methods=['POST'])
@login_required
def cancel_scheduled_message(msg_id):
    """Cancel a scheduled message"""
    try:
        scheduled_msg = ScheduledMessage.query.filter_by(
            id=msg_id, 
            user_id=current_user.id
        ).first()
        
        if not scheduled_msg:
            return jsonify({'error': 'Scheduled message not found'}), 404
        
        if scheduled_msg.status != 'pending':
            return jsonify({'error': 'Can only cancel pending messages'}), 400
        
        scheduled_msg.status = 'cancelled'
        db.session.commit()
        
        logger.info(f"❌ Scheduled message cancelled: {msg_id}")
        
        return jsonify({
            'success': True,
            'message': 'Scheduled message cancelled successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Cancel scheduled message error: {str(e)}")
        return jsonify({'error': 'Failed to cancel scheduled message'}), 500

@messaging_api.route('/message-history', methods=['GET'])
@login_required
def get_message_history():
    """Get message history with pagination"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status_filter = request.args.get('status')
        
        query = MessageHistory.query.filter_by(user_id=current_user.id)
        
        if status_filter:
            query = query.filter(MessageHistory.status == status_filter)
        
        messages = query.order_by(MessageHistory.created_at.desc())\
            .offset((page - 1) * per_page).limit(per_page).all()
        
        total_count = query.count()
        
        return jsonify({
            'success': True,
            'messages': [{
                'id': msg.id,
                'recipient': msg.recipient,
                'recipient_name': msg.recipient_name,
                'template_id': msg.template_id,
                'template_name': msg.template.name if msg.template else None,
                'message_content': msg.message_content,
                'message_type': msg.message_type,
                'status': msg.status,
                'meta_message_id': msg.meta_message_id,
                'created_at': msg.created_at.isoformat()
            } for msg in messages],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total_count,
                'pages': (total_count + per_page - 1) // per_page
            }
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Get message history error: {str(e)}")
        return jsonify({'error': 'Failed to load message history'}), 500