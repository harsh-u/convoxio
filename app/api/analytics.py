import logging
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import MessageHistory, Template, Contact
from datetime import datetime, timedelta
from sqlalchemy import func, and_

logger = logging.getLogger(__name__)

analytics_api = Blueprint('analytics_api', __name__)

@analytics_api.route('/analytics', methods=['GET'])
@login_required
def get_analytics():
    """Get comprehensive analytics data"""
    try:
        if current_user.onboarding_status != 'Verified':
            return jsonify({'error': 'WhatsApp setup not completed'}), 400
        
        # Date range for analytics (last 30 days by default)
        days = request.args.get('days', 30, type=int)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Basic stats
        total_messages = MessageHistory.query.filter_by(user_id=current_user.id).count()
        messages_this_period = MessageHistory.query.filter(
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
        
        # Daily message counts
        daily_stats = []
        for i in range(min(days, 30)):  # Limit to 30 days for performance
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
         .limit(10).all()
        
        # Calculate delivery and read rates
        delivered_count = MessageHistory.query.filter_by(user_id=current_user.id, status='delivered').count()
        read_count = MessageHistory.query.filter_by(user_id=current_user.id, status='read').count()
        
        delivery_rate = (delivered_count / total_messages * 100) if total_messages > 0 else 0
        read_rate = (read_count / total_messages * 100) if total_messages > 0 else 0
        
        # Contact stats
        total_contacts = Contact.query.filter_by(user_id=current_user.id).count()
        
        # Recent activity (last 7 days)
        week_ago = end_date - timedelta(days=7)
        recent_messages = MessageHistory.query.filter(
            and_(
                MessageHistory.user_id == current_user.id,
                MessageHistory.created_at >= week_ago
            )
        ).count()
        
        return jsonify({
            'success': True,
            'analytics': {
                'overview': {
                    'total_messages': total_messages,
                    'messages_this_period': messages_this_period,
                    'delivery_rate': round(delivery_rate, 1),
                    'read_rate': round(read_rate, 1),
                    'remaining_messages': current_user.get_remaining_messages(),
                    'total_contacts': total_contacts,
                    'recent_messages': recent_messages
                },
                'daily_stats': daily_stats,
                'status_breakdown': [{'status': status, 'count': count} for status, count in status_stats],
                'template_performance': [{'name': name, 'usage_count': count} for name, count in template_stats],
                'period_days': days
            }
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Analytics error: {str(e)}")
        return jsonify({'error': 'Failed to load analytics'}), 500

@analytics_api.route('/analytics/summary', methods=['GET'])
@login_required
def get_analytics_summary():
    """Get quick analytics summary for dashboard"""
    try:
        if current_user.onboarding_status != 'Verified':
            return jsonify({'error': 'WhatsApp setup not completed'}), 400
        
        # Get basic counts
        total_messages = MessageHistory.query.filter_by(user_id=current_user.id).count()
        total_templates = Template.query.filter_by(user_id=current_user.id).count()
        approved_templates = Template.query.filter_by(user_id=current_user.id, status='Approved').count()
        total_contacts = Contact.query.filter_by(user_id=current_user.id).count()
        
        # Today's stats
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        messages_today = MessageHistory.query.filter(
            and_(
                MessageHistory.user_id == current_user.id,
                MessageHistory.created_at >= today
            )
        ).count()
        
        # This week's stats
        week_start = today - timedelta(days=today.weekday())
        messages_this_week = MessageHistory.query.filter(
            and_(
                MessageHistory.user_id == current_user.id,
                MessageHistory.created_at >= week_start
            )
        ).count()
        
        # This month's stats
        month_start = today.replace(day=1)
        messages_this_month = MessageHistory.query.filter(
            and_(
                MessageHistory.user_id == current_user.id,
                MessageHistory.created_at >= month_start
            )
        ).count()
        
        # Status counts
        delivered_count = MessageHistory.query.filter_by(user_id=current_user.id, status='delivered').count()
        read_count = MessageHistory.query.filter_by(user_id=current_user.id, status='read').count()
        failed_count = MessageHistory.query.filter_by(user_id=current_user.id, status='failed').count()
        
        return jsonify({
            'success': True,
            'summary': {
                'totals': {
                    'messages': total_messages,
                    'templates': total_templates,
                    'approved_templates': approved_templates,
                    'contacts': total_contacts
                },
                'time_periods': {
                    'today': messages_today,
                    'this_week': messages_this_week,
                    'this_month': messages_this_month
                },
                'status_counts': {
                    'delivered': delivered_count,
                    'read': read_count,
                    'failed': failed_count
                },
                'rates': {
                    'delivery_rate': round((delivered_count / total_messages * 100) if total_messages > 0 else 0, 1),
                    'read_rate': round((read_count / total_messages * 100) if total_messages > 0 else 0, 1),
                    'failure_rate': round((failed_count / total_messages * 100) if total_messages > 0 else 0, 1)
                },
                'usage': {
                    'remaining_messages': current_user.get_remaining_messages(),
                    'usage_percentage': round((current_user.messages_sent_this_month / current_user.message_limit * 100) if current_user.message_limit > 0 else 0, 1)
                }
            }
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Analytics summary error: {str(e)}")
        return jsonify({'error': 'Failed to load analytics summary'}), 500

@analytics_api.route('/analytics/templates', methods=['GET'])
@login_required
def get_template_analytics():
    """Get detailed template performance analytics"""
    try:
        # Template usage with detailed stats
        template_analytics = db.session.query(
            Template.id,
            Template.name,
            Template.status,
            Template.category,
            Template.created_at,
            func.count(MessageHistory.id).label('total_sent'),
            func.sum(func.case([(MessageHistory.status == 'delivered', 1)], else_=0)).label('delivered'),
            func.sum(func.case([(MessageHistory.status == 'read', 1)], else_=0)).label('read'),
            func.sum(func.case([(MessageHistory.status == 'failed', 1)], else_=0)).label('failed')
        ).outerjoin(MessageHistory, Template.id == MessageHistory.template_id)\
         .filter(Template.user_id == current_user.id)\
         .group_by(Template.id)\
         .order_by(func.count(MessageHistory.id).desc()).all()
        
        templates_data = []
        for t in template_analytics:
            total_sent = t.total_sent or 0
            delivered = t.delivered or 0
            read = t.read or 0
            failed = t.failed or 0
            
            templates_data.append({
                'id': t.id,
                'name': t.name,
                'status': t.status,
                'category': t.category,
                'created_at': t.created_at.isoformat(),
                'stats': {
                    'total_sent': total_sent,
                    'delivered': delivered,
                    'read': read,
                    'failed': failed,
                    'delivery_rate': round((delivered / total_sent * 100) if total_sent > 0 else 0, 1),
                    'read_rate': round((read / total_sent * 100) if total_sent > 0 else 0, 1),
                    'failure_rate': round((failed / total_sent * 100) if total_sent > 0 else 0, 1)
                }
            })
        
        return jsonify({
            'success': True,
            'template_analytics': templates_data
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Template analytics error: {str(e)}")
        return jsonify({'error': 'Failed to load template analytics'}), 500