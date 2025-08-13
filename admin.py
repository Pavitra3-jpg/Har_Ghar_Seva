from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import users_db, jobs_db, applications_db

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.user_type != 'admin':
        flash('Access denied.', 'error')
        return redirect(url_for('index'))
    
    # Get statistics
    total_users = len(users_db)
    total_workers = len([u for u in users_db.values() if u.user_type == 'worker'])
    total_providers = len([u for u in users_db.values() if u.user_type == 'provider'])
    total_jobs = len(jobs_db)
    pending_verifications = len([u for u in users_db.values() if u.user_type == 'worker' and not u.is_verified])
    
    # Get recent users and jobs
    recent_users = sorted(users_db.values(), key=lambda x: x.created_at, reverse=True)[:10]
    recent_jobs = sorted(jobs_db.values(), key=lambda x: x.created_at, reverse=True)[:10]
    
    return render_template('admin/dashboard.html', 
                         total_users=total_users,
                         total_workers=total_workers,
                         total_providers=total_providers,
                         total_jobs=total_jobs,
                         pending_verifications=pending_verifications,
                         recent_users=recent_users,
                         recent_jobs=recent_jobs)

@admin_bp.route('/users')
@login_required
def users():
    if current_user.user_type != 'admin':
        flash('Access denied.', 'error')
        return redirect(url_for('index'))
    
    user_type_filter = request.args.get('type', 'all')
    verification_filter = request.args.get('verification', 'all')
    
    all_users = list(users_db.values())
    
    # Apply filters
    if user_type_filter != 'all':
        all_users = [u for u in all_users if u.user_type == user_type_filter]
    
    if verification_filter == 'verified':
        all_users = [u for u in all_users if u.is_verified]
    elif verification_filter == 'pending':
        all_users = [u for u in all_users if not u.is_verified and u.user_type == 'worker']
    
    return render_template('admin/users.html', users=all_users, 
                         user_type_filter=user_type_filter,
                         verification_filter=verification_filter)

@admin_bp.route('/verify_user/<int:user_id>')
@login_required
def verify_user(user_id):
    if current_user.user_type != 'admin':
        flash('Access denied.', 'error')
        return redirect(url_for('index'))
    
    user = users_db.get(user_id)
    if user:
        user.is_verified = True
        flash(f'User {user.username} has been verified.', 'success')
    else:
        flash('User not found.', 'error')
    
    return redirect(url_for('admin.users'))

@admin_bp.route('/reject_user/<int:user_id>')
@login_required
def reject_user(user_id):
    if current_user.user_type != 'admin':
        flash('Access denied.', 'error')
        return redirect(url_for('index'))
    
    user = users_db.get(user_id)
    if user and user.user_type == 'worker':
        # In a real app, you might want to soft delete or mark as rejected
        # For now, we'll just remove from database
        del users_db[user_id]
        flash(f'User account has been rejected and removed.', 'success')
    else:
        flash('User not found or cannot be rejected.', 'error')
    
    return redirect(url_for('admin.users'))
