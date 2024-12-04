from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from app.models.user import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        user = User.get_by_email(email)
        if user and check_password_hash(user.password_hash, password):
            login_user(user, remember=remember)
            # Redirect based on user role
            if user.role_type == 'host':
                return redirect(url_for('host.dashboard'))
            else:
                return redirect(url_for('traveler.dashboard'))
            
        flash('Please check your login details and try again.')
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Get form data
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        password = request.form.get('password')
        user_type = request.form.get('user_type')
        terms = request.form.get('terms')
        
        # Basic validation
        if not all([first_name, last_name, email, password, user_type, terms]):
            flash('Please fill in all required fields.')
            return redirect(url_for('auth.register'))
        
        # Check if user already exists
        if User.get_by_email(email):
            flash('Email address already exists')
            return redirect(url_for('auth.register'))
        
        # Create username from first and last name
        username = f"{first_name.lower()}_{last_name.lower()}"
        
        try:
            # Create new user
            password_hash = generate_password_hash(password)
            
            print(f"Attempting to create user with username: {username}, email: {email}, role: {user_type}")
            
            user_id = User.create_user(
                username=username,
                first_name=first_name,
                last_name=last_name,
                email=email,
                password_hash=password_hash,
                role_type=user_type
            )
            
            if user_id:
                flash('Registration successful! Please log in.')
                return redirect(url_for('auth.login'))
            else:
                flash('Registration failed. Please try again.')
                
        except Exception as e:
            print(f"Error during registration: {str(e)}")
            flash('An error occurred during registration.')
            
        return redirect(url_for('auth.register'))
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))