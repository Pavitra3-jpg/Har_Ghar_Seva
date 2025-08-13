from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from models import create_user, get_user_by_email, get_user_by_username

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = get_user_by_email(email)
        
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            
            # Redirect based on user type
            if user.user_type == 'admin':
                return redirect(url_for('admin.dashboard'))
            elif user.user_type == 'worker':
                return redirect(url_for('worker.dashboard'))
            else:  # provider
                return redirect(url_for('jobs.my_jobs'))
        else:
            flash('Invalid email or password.', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        user_type = request.form.get('user_type', 'worker')
        
        # Validation
        if not all([username, email, password, confirm_password]):
            flash('All fields are required.', 'error')
            return render_template('auth/register.html')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('auth/register.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'error')
            return render_template('auth/register.html')
        
        # Check if user already exists
        if get_user_by_email(email):
            flash('Email already registered.', 'error')
            return render_template('auth/register.html')
        
        if get_user_by_username(username):
            flash('Username already taken.', 'error')
            return render_template('auth/register.html')
        
        # Create user
        user = create_user(username, email, password, user_type)
        login_user(user)
        
        if user_type == 'worker':
            flash('Account created! Please complete your profile to start receiving job matches.', 'success')
            return redirect(url_for('worker.profile'))
        else:
            flash('Account created successfully!', 'success')
            return redirect(url_for('jobs.browse'))
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))
