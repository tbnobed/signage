import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, Response
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from app import app, db, login_manager
from models import User

auth = Blueprint('auth', __name__)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('auth.login'))

# Setup route removed for security - use create_admin.py script instead

# ========================================
# USER MANAGEMENT ROUTES
# ========================================

@auth.route('/users')
@login_required
def users():
    """List all users - admin access required"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('users.html', users=users)

@auth.route('/users/add', methods=['GET', 'POST'])
@login_required
def add_user():
    """Add a new user - admin access required"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip()
        password = request.form['password']
        is_admin = 'is_admin' in request.form
        
        # Validation
        if not username or not email or not password:
            flash('All fields are required.', 'error')
            return render_template('add_user.html')
        
        # Check if username already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists. Please choose a different username.', 'error')
            return render_template('add_user.html')
        
        # Check if email already exists
        if User.query.filter_by(email=email).first():
            flash('Email address already exists. Please use a different email.', 'error')
            return render_template('add_user.html')
        
        try:
            # Create new user
            new_user = User(
                username=username,
                email=email,
                is_admin=is_admin
            )
            new_user.set_password(password)
            
            db.session.add(new_user)
            db.session.commit()
            
            flash(f'User "{username}" has been created successfully.', 'success')
            return redirect(url_for('auth.users'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating user: {str(e)}', 'error')
    
    return render_template('add_user.html')

@auth.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    """Edit user details - admin access required"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip()
        is_admin = 'is_admin' in request.form
        
        # Validation
        if not username or not email:
            flash('Username and email are required.', 'error')
            return render_template('edit_user.html', user=user)
        
        # Check if username already exists (but not the current user)
        existing_user = User.query.filter_by(username=username).first()
        if existing_user and existing_user.id != user.id:
            flash('Username already exists. Please choose a different username.', 'error')
            return render_template('edit_user.html', user=user)
        
        # Check if email already exists (but not the current user)
        existing_user = User.query.filter_by(email=email).first()
        if existing_user and existing_user.id != user.id:
            flash('Email address already exists. Please use a different email.', 'error')
            return render_template('edit_user.html', user=user)
        
        try:
            # Update user
            user.username = username
            user.email = email
            user.is_admin = is_admin
            
            db.session.commit()
            
            flash(f'User "{username}" has been updated successfully.', 'success')
            return redirect(url_for('auth.users'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating user: {str(e)}', 'error')
    
    return render_template('edit_user.html', user=user)

@auth.route('/users/<int:user_id>/change-password', methods=['GET', 'POST'])
@login_required
def change_password(user_id):
    """Change user password - admin access required"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        
        # Validation
        if not new_password or not confirm_password:
            flash('Both password fields are required.', 'error')
            return render_template('change_password.html', user=user)
        
        if new_password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('change_password.html', user=user)
        
        if len(new_password) < 6:
            flash('Password must be at least 6 characters long.', 'error')
            return render_template('change_password.html', user=user)
        
        try:
            # Update password
            user.set_password(new_password)
            db.session.commit()
            
            flash(f'Password for "{user.username}" has been updated successfully.', 'success')
            return redirect(url_for('auth.users'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating password: {str(e)}', 'error')
    
    return render_template('change_password.html', user=user)

@auth.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    """Delete a user - admin access required"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    user = User.query.get_or_404(user_id)
    
    # Prevent self-deletion
    if user.id == current_user.id:
        flash('You cannot delete your own account.', 'error')
        return redirect(url_for('auth.users'))
    
    # Check if this is the last admin user
    admin_count = User.query.filter_by(is_admin=True).count()
    if user.is_admin and admin_count <= 1:
        flash('Cannot delete the last admin user. Please create another admin first.', 'error')
        return redirect(url_for('auth.users'))
    
    try:
        username = user.username
        db.session.delete(user)
        db.session.commit()
        
        flash(f'User "{username}" has been deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting user: {str(e)}', 'error')
    
    return redirect(url_for('auth.users'))

@auth.route('/client-setup')
def client_setup():
    """Serve the Python client setup script for download"""
    try:
        # Read the setup_client.py file
        with open('setup_client.py', 'r') as f:
            script_content = f.read()
        
        # Return as downloadable file
        return Response(
            script_content,
            mimetype='text/plain',
            headers={
                'Content-Disposition': 'attachment; filename=setup_client.py',
                'Content-Type': 'text/plain; charset=utf-8'
            }
        )
    except FileNotFoundError:
        flash('Setup script not found. Please contact your administrator.', 'error')
        return redirect(url_for('auth.login'))

@auth.route('/client-setup-sh')
def client_setup_sh():
    """Serve the shell wrapper script for curl installation"""
    try:
        # Read the setup_client.sh file
        with open('setup_client.sh', 'r') as f:
            script_content = f.read()
        
        # Return as text for curl piping
        return Response(
            script_content,
            mimetype='text/plain',
            headers={
                'Content-Type': 'text/plain; charset=utf-8'
            }
        )
    except FileNotFoundError:
        flash('Shell setup script not found. Please contact your administrator.', 'error')
        return redirect(url_for('auth.login'))
