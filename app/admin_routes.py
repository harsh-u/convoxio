import logging
from flask import Blueprint, render_template, redirect, url_for, request, flash
from app.models import User, Upload, SubscriptionPlan, UserSubscription, Payment, MessageHistory, Template
from app import db
from datetime import datetime, timedelta
from sqlalchemy import func, and_

# Create logger for admin routes
logger = logging.getLogger(__name__)

admin = Blueprint('admin', __name__)

ADMIN_EMAIL = "admin@yourapp.com"
ADMIN_PASSWORD = "admin123"  # You can hash it or add proper admin login later

@admin.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    logger.info("👑 Admin login page accessed")
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        logger.info(f"👑 Admin login attempt for email: {email}")
        if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
            logger.info("✅ Admin login successful")
            return redirect(url_for('admin.admin_dashboard'))
        logger.warning(f"❌ Failed admin login attempt for email: {email}")
        flash('Invalid admin credentials', 'danger')
    return render_template('admin_login.html')

@admin.route('/admin/dashboard')
def admin_dashboard():
    logger.info("👑 Admin dashboard accessed")
    # Get key metrics for dashboard
    total_users = User.query.count()
    active_subscriptions = UserSubscription.query.filter_by(status='active').count()
    total_revenue = db.session.query(func.sum(Payment.amount)).filter_by(status='completed').scalar() or 0
    messages_sent_today = MessageHistory.query.filter(
        MessageHistory.created_at >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    ).count()
    
    logger.info(f"📊 Dashboard metrics - Users: {total_users}, Active Subs: {active_subscriptions}, Revenue: ${total_revenue}, Messages Today: {messages_sent_today}")
    
    # Recent activity
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_payments = Payment.query.filter_by(status='completed').order_by(Payment.created_at.desc()).limit(5).all()
    
    # Monthly stats
    current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_revenue = db.session.query(func.sum(Payment.amount)).filter(
        and_(Payment.status == 'completed', Payment.created_at >= current_month)
    ).scalar() or 0
    
    monthly_users = User.query.filter(User.created_at >= current_month).count()
    
    return render_template('admin_dashboard.html', 
                         total_users=total_users,
                         active_subscriptions=active_subscriptions,
                         total_revenue=total_revenue,
                         messages_sent_today=messages_sent_today,
                         recent_users=recent_users,
                         recent_payments=recent_payments,
                         monthly_revenue=monthly_revenue,
                         monthly_users=monthly_users)

@admin.route('/admin/users')
def admin_users():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    status_filter = request.args.get('status', '')
    
    query = User.query
    
    if search:
        query = query.filter(User.email.contains(search) | User.business_name.contains(search))
    
    if status_filter:
        query = query.filter(User.onboarding_status == status_filter)
    
    users = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin_users.html', users=users, search=search, status_filter=status_filter)

@admin.route('/admin/user/<int:user_id>')
def view_user(user_id):
    user = User.query.get_or_404(user_id)
    uploads = Upload.query.filter_by(user_id=user.id).all()
    templates = Template.query.filter_by(user_id=user.id).all()
    messages = MessageHistory.query.filter_by(user_id=user.id).order_by(MessageHistory.created_at.desc()).limit(10).all()
    payments = Payment.query.filter_by(user_id=user.id).order_by(Payment.created_at.desc()).all()
    
    return render_template('admin_view_user.html', 
                         user=user, 
                         uploads=uploads, 
                         templates=templates,
                         messages=messages,
                         payments=payments)

@admin.route('/admin/user/<int:user_id>/status/<status>')
def update_status(user_id, status):
    if status not in ['Pending', 'In Progress', 'Verified']:
        flash('Invalid status', 'danger')
        return redirect(url_for('admin.view_user', user_id=user_id))
    user = User.query.get_or_404(user_id)
    user.onboarding_status = status
    db.session.commit()
    flash(f'Status updated to {status}', 'success')
    return redirect(url_for('admin.view_user', user_id=user_id))

@admin.route('/admin/payments')
def admin_payments():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    
    query = Payment.query
    
    if status_filter:
        query = query.filter(Payment.status == status_filter)
    
    payments = query.order_by(Payment.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin_payments.html', payments=payments, status_filter=status_filter)

@admin.route('/admin/templates')
def admin_templates():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    
    query = Template.query
    
    if status_filter:
        query = query.filter(Template.status == status_filter)
    
    templates = query.order_by(Template.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin_templates.html', templates=templates, status_filter=status_filter)

@admin.route('/admin/template/<int:template_id>/approve')
def approve_template(template_id):
    template = Template.query.get_or_404(template_id)
    template.status = 'Approved'
    db.session.commit()
    flash(f'Template "{template.name}" approved successfully!', 'success')
    return redirect(url_for('admin.admin_templates'))

@admin.route('/admin/template/<int:template_id>/reject')
def reject_template(template_id):
    template = Template.query.get_or_404(template_id)
    template.status = 'Rejected'
    db.session.commit()
    flash(f'Template "{template.name}" rejected.', 'warning')
    return redirect(url_for('admin.admin_templates'))

@admin.route('/admin/analytics')
def admin_analytics():
    # Revenue analytics
    revenue_by_month = db.session.query(
        func.date_format(Payment.created_at, '%Y-%m').label('month'),
        func.sum(Payment.amount).label('revenue')
    ).filter_by(status='completed').group_by('month').order_by('month').all()
    
    # User growth
    user_growth = db.session.query(
        func.date_format(User.created_at, '%Y-%m').label('month'),
        func.count(User.id).label('users')
    ).group_by('month').order_by('month').all()
    
    # Plan distribution
    plan_distribution = db.session.query(
        SubscriptionPlan.name,
        func.count(UserSubscription.id).label('count')
    ).join(UserSubscription, SubscriptionPlan.id == UserSubscription.plan_id)\
     .filter(UserSubscription.status == 'active')\
     .group_by(SubscriptionPlan.name).all()
    
    # Message volume
    message_volume = db.session.query(
        func.date_format(MessageHistory.created_at, '%Y-%m-%d').label('date'),
        func.count(MessageHistory.id).label('messages')
    ).filter(MessageHistory.created_at >= datetime.now() - timedelta(days=30))\
     .group_by('date').order_by('date').all()
    
    return render_template('admin_analytics.html',
                         revenue_by_month=revenue_by_month,
                         user_growth=user_growth,
                         plan_distribution=plan_distribution,
                         message_volume=message_volume)
