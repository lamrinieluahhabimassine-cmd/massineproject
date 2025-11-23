"""
Authentication routes: login, register, logout
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User
from utils.validation import Validator, ValidationError

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def index():
    """Landing page"""
    if current_user.is_authenticated:
        # Redirect based on role
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif current_user.role == 'invoicing':
            return redirect(url_for('invoice.dashboard'))
        elif current_user.role == 'affecteur':
            return redirect(url_for('affecteur.dashboard'))
        elif current_user.role == 'évaluateur':
            return redirect(url_for('evaluator.dashboard'))
        else:
            return redirect(url_for('user.dashboard'))
    return render_template('auth/index.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        # Redirect based on role
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif current_user.role == 'invoicing':
            return redirect(url_for('invoice.dashboard'))
        elif current_user.role == 'affecteur':
            return redirect(url_for('affecteur.dashboard'))
        elif current_user.role == 'évaluateur':
            return redirect(url_for('evaluator.dashboard'))
        else:
            return redirect(url_for('user.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        # Validation
        if not username or not password:
            flash('Tous les champs sont requis.', 'danger')
            return render_template('auth/login.html')
        
        # Check user exists
        user = User.query.filter_by(username=username).first()
        
        if not user or not user.check_password(password):
            flash('Nom d\'utilisateur ou mot de passe incorrect.', 'danger')
            return render_template('auth/login.html')
        
        # Check if user is active
        if not user.is_active:
            flash('Votre compte a été désactivé. Contactez l\'administrateur.', 'danger')
            return render_template('auth/login.html')
        
        # Login successful
        login_user(user)
        flash(f'Bienvenue, {user.username}!', 'success')
        
        # Redirect based on role
        if user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif user.role == 'invoicing':
            return redirect(url_for('invoice.dashboard'))
        elif user.role == 'affecteur':
            return redirect(url_for('affecteur.dashboard'))
        elif user.role == 'évaluateur':
            return redirect(url_for('evaluator.dashboard'))
        else:
            return redirect(url_for('user.dashboard'))
    return render_template('auth/login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('user.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')  # ⚠️ NE PAS strip() le mot de passe
        confirm_password = request.form.get('confirm_password', '')  # ⚠️ NE PAS strip()
        
        # Validate
        try:
            Validator.validate_username(username)
            Validator.validate_email(email)
            Validator.validate_password(password)
            
            # Check password match
            if password != confirm_password:
                raise ValidationError("Les mots de passe ne correspondent pas.")
            # Check if username exists
            if User.query.filter_by(username=username).first():
                raise ValidationError("Ce nom d'utilisateur existe déjà.")
            
            # Check if email exists
            if User.query.filter_by(email=email.lower()).first():
                raise ValidationError("Cet email est déjà utilisé.")
            
            # Create user
            new_user = User(
                username=username,
                email=email.lower(),
                role='user'  # Default role
            )
            new_user.set_password(password)
            
            db.session.add(new_user)
            db.session.commit()
            
            flash('Inscription réussie! Vous pouvez maintenant vous connecter.', 'success')
            return redirect(url_for('auth.login'))
            
        except ValidationError as e:
            flash(str(e), 'danger')
            return render_template('auth/register.html')
    
    return render_template('auth/register.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('Vous avez été déconnecté avec succès.', 'info')
    return redirect(url_for('auth.index'))