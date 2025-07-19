from flask import Blueprint, render_template, redirect, url_for, request, flash
from app.models import User, Upload
from app import db

admin = Blueprint('admin', __name__)

ADMIN_EMAIL = "admin@yourapp.com"
ADMIN_PASSWORD = "admin123"  # You can hash it or add proper admin login later

@admin.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
            return redirect(url_for('admin.admin_dashboard'))
        flash('Invalid admin credentials', 'danger')
    return render_template('admin_login.html')

@admin.route('/admin/dashboard')
def admin_dashboard():
    users = User.query.all()
    return render_template('admin_dashboard.html', users=users)

@admin.route('/admin/user/<int:user_id>')
def view_user(user_id):
    user = User.query.get_or_404(user_id)
    uploads = Upload.query.filter_by(user_id=user.id).all()
    return render_template('admin_view_user.html', user=user, uploads=uploads)

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
