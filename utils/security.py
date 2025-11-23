"""
Security improvements and utilities
"""
from functools import wraps
from flask import abort, request
from flask_login import current_user
import secrets
import string

# CSRF Protection would be handled by Flask-WTF in forms

def generate_secure_token(length=32):
    """Generate a secure random token"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def rate_limit_login(max_attempts=5, window_minutes=15):
    """
    Rate limiting decorator for login attempts
    Store attempts in a simple dict (use Redis in production)
    """
    attempts = {}
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            ip = request.remote_addr
            current_time = datetime.now()
            
            # Clean old attempts
            if ip in attempts:
                attempts[ip] = [t for t in attempts[ip] 
                               if (current_time - t).seconds < window_minutes * 60]
            
            # Check if rate limited
            if ip in attempts and len(attempts[ip]) >= max_attempts:
                abort(429, "Too many login attempts. Please try again later.")
            
            # Record attempt
            if ip not in attempts:
                attempts[ip] = []
            attempts[ip].append(current_time)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f):
    """Enhanced admin check with better error handling"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(401, "Authentication required")
        if not current_user.is_admin():
            abort(403, "Admin privileges required")
        return f(*args, **kwargs)
    return decorated_function


def owner_or_admin_required(model_class, id_param='file_id'):
    """
    Check if user owns the resource or is admin
    Usage: @owner_or_admin_required(File, 'file_id')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            
            resource_id = kwargs.get(id_param)
            resource = model_class.query.get_or_404(resource_id)
            
            # Check ownership
            if hasattr(resource, 'user_id'):
                if resource.user_id != current_user.id and not current_user.is_admin():
                    abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def sanitize_filename(filename):
    """Sanitize uploaded filenames"""
    import os
    from werkzeug.utils import secure_filename
    return secure_filename(filename)


def validate_email(email):
    """Basic email validation"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def check_password_strength(password):
    """
    Check password strength
    Returns: (bool, str) - (is_valid, message)
    """
    if len(password) < 8:
        return False, "Le mot de passe doit contenir au moins 8 caractères"
    
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    
    if not (has_upper and has_lower and has_digit):
        return False, "Le mot de passe doit contenir majuscules, minuscules et chiffres"
    
    return True, "Mot de passe valide"


# Security headers middleware
def add_security_headers(response):
    """Add security headers to all responses"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response