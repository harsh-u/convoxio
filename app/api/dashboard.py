import logging
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import User, Upload, Template, MessageHistory, Contact
from datetime import datetime, timedelta
from sqlalchemy import func, and_

logger = logging.getLogger(__name__)

dashboard_api = Blueprint('dashboard_api', __name__)

@dashboard_api.route('/dashboard', methods=['GET'])
@login_required
def get_dashboard_data():
    """Get dashboard data for mobile app"""
    try:
        logger.info(f"📊 API Dashboard accessed by user: {current_user.email} (ID: {current_user.id})")
        
        # Get uploads
        uploads = Upload.query.filter_by(user_id=current_user.id).all()
        has_pan = any(u.filetype == 'PAN' for u in uploads)
        has_gst = any(u.filetype == 'GST' for u in uploads)
        docs_uploaded = has_pan and has_gst
        
        # Check if user can send messages
        approved_templates = Template.query.filter_by(user_id=current_user.id, status='Approved').all()
        can_send = (current_user.onboarding_status == 'Verified' and 
                    current_user.whatsapp_access_token and 
                    current_user.phone_number_id and 
                    approved_templates)
        
        # Get recent message history
        message_history = MessageHistory.query.filter_by(user_id=current_user.id)\
            .order_by(MessageHistory.created_at.desc()).limit(10).all()
        
        # Get template count
        template_count = Template.query.filter_by(user_id=current_user.id).count()
        approved_template_count = len(approved_templates)
        
        # Get contact count
        contact_count = Contact.query.filter_by(user_id=current_user.id).count()
        
        # Get today's message count
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        messages_today = MessageHistory.query.filter(
            and_(
                MessageHistory.user_id == current_user.id,
                MessageHistory.created_at >= today
            )
        ).count()
        
        logger.info(f"📋 User status - Docs uploaded: {docs_uploaded}, Can send: {can_send}")
        
        return jsonify({
            'success': True,
            'data': {
                'user': {
                    'id': current_user.id,
                    'email': current_user.email,
                    'business_name': current_user.business_name,
                    'onboarding_status': current_user.onboarding_status,
                    'message_limit': current_user.message_limit,
                    'messages_sent_this_month': current_user.messages_sent_this_month,
                    'remaining_messages': current_user.get_remaining_messages(),
                    'is_verified': current_user.is_verified
                },
                'setup_status': {
                    'docs_uploaded': docs_uploaded,
                    'has_pan': has_pan,
                    'has_gst': has_gst,
                    'can_send': can_send,
                    'whatsapp_connected': current_user.onboarding_status == 'Verified'
                },
                'stats': {
                    'total_messages': MessageHistory.query.filter_by(user_id=current_user.id).count(),
                    'messages_today': messages_today,
                    'template_count': template_count,
                    'approved_templates': approved_template_count,
                    'contact_count': contact_count
                },
                'recent_messages': [{
                    'id': msg.id,
                    'recipient': msg.recipient,
                    'recipient_name': msg.recipient_name,
                    'template_id': msg.template_id,
                    'message_content': msg.message_content,
                    'status': msg.status,
                    'created_at': msg.created_at.isoformat(),
                    'template_name': msg.template.name if msg.template else None
                } for msg in message_history],
                'uploads': [{
                    'id': upload.id,
                    'filename': upload.filename,
                    'filetype': upload.filetype
                } for upload in uploads]
            }
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Dashboard API error: {str(e)}")
        return jsonify({'error': 'Failed to load dashboard data'}), 500

@dashboard_api.route('/quick-stats', methods=['GET'])
@login_required
def get_quick_stats():
    """Get quick stats for dashboard widgets"""
    try:
        # Get date ranges
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        this_week = today - timedelta(days=7)
        this_month = today.replace(day=1)
        
        # Message stats
        total_messages = MessageHistory.query.filter_by(user_id=current_user.id).count()
        messages_today = MessageHistory.query.filter(
            and_(MessageHistory.user_id == current_user.id, MessageHistory.created_at >= today)
        ).count()
        messages_this_week = MessageHistory.query.filter(
            and_(MessageHistory.user_id == current_user.id, MessageHistory.created_at >= this_week)
        ).count()
        messages_this_month = MessageHistory.query.filter(
            and_(MessageHistory.user_id == current_user.id, MessageHistory.created_at >= this_month)
        ).count()
        
        # Status breakdown
        status_stats = db.session.query(
            MessageHistory.status,
            func.count(MessageHistory.id).label('count')
        ).filter_by(user_id=current_user.id).group_by(MessageHistory.status).all()
        
        # Calculate rates
        delivered_count = MessageHistory.query.filter_by(user_id=current_user.id, status='delivered').count()
        read_count = MessageHistory.query.filter_by(user_id=current_user.id, status='read').count()
        
        delivery_rate = (delivered_count / total_messages * 100) if total_messages > 0 else 0
        read_rate = (read_count / total_messages * 100) if total_messages > 0 else 0
        
        return jsonify({
            'success': True,
            'stats': {
                'total_messages': total_messages,
                'messages_today': messages_today,
                'messages_this_week': messages_this_week,
                'messages_this_month': messages_this_month,
                'delivery_rate': round(delivery_rate, 1),
                'read_rate': round(read_rate, 1),
                'remaining_messages': current_user.get_remaining_messages(),
                'status_breakdown': [{'status': status, 'count': count} for status, count in status_stats]
            }
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Quick stats API error: {str(e)}")
        return jsonify({'error': 'Failed to load stats'}), 500