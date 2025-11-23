"""
Validation utilities for file and user data
"""
from datetime import date, datetime


class ValidationError(Exception):
    """Custom validation error"""
    pass


class Validator:
    """Validator class for all validation methods"""
    
    @staticmethod
    def validate_non_empty(value, field_name):
        """Validate that a field is not empty"""
        if not value or not value.strip():
            raise ValidationError(f"{field_name} est requis.")
        return value.strip()
    
    @staticmethod
    def validate_file_number(file_number):
        """Validate file number format"""
        if not file_number or not file_number.strip():
            raise ValidationError("Numéro de dossier requis.")
        
        file_number = file_number.strip()
        
        if len(file_number) < 3 or len(file_number) > 100:
            raise ValidationError("Numéro de dossier doit contenir entre 3 et 100 caractères.")
        
        return file_number
    
    @staticmethod
    def validate_date_string(date_str, field_name):
        """Validate date string format (YYYY-MM-DD)"""
        if not date_str or not date_str.strip():
            raise ValidationError(f"{field_name} est requis.")
        
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            raise ValidationError(f"Format de date invalide pour {field_name}. Utilisez YYYY-MM-DD.")
        
        return date_str
    
    @staticmethod
    def validate_route(route, sor_number, sol_number):
        """Validate route and associated numbers"""
        if route not in ['A', 'B', 'C']:
            raise ValidationError("Route invalide. Choisissez A, B ou C.")
        
        if route == 'B':
            if not sor_number or not sor_number.strip():
                raise ValidationError("Numéro SOR requis pour Route B.")
        
        if route == 'C':
            if not sol_number or not sol_number.strip():
                raise ValidationError("Numéro SOL requis pour Route C.")
        
        return route
    
    @staticmethod
    def validate_status(status):
        """Validate status"""
        valid_statuses = [
            'en attente d\'évaluation',
            'en cours d\'évaluation',
            'ready to invoice',
            'payed',
            'en cours de traitement',
            'à compléter',
            'transfert à l\'inspection',
            'Finalized'
        ]
        
        if status not in valid_statuses:
            raise ValidationError("Statut invalide.")
        
        return status
    
    @staticmethod
    def validate_recall_date(recall_date):
        """Validate recall date (should not be too far in the past)"""
        if recall_date:
            if isinstance(recall_date, str):
                recall_date = datetime.strptime(recall_date, '%Y-%m-%d').date()
            
            # Allow past dates but warn if more than 1 year in the past
            one_year_ago = date.today().replace(year=date.today().year - 1)
            if recall_date < one_year_ago:
                raise ValidationError("Date de rappel trop ancienne (plus d'un an dans le passé).")
        
        return recall_date
    
    @staticmethod
    def validate_email(email):
        """Validate email format"""
        if not email or not email.strip():
            raise ValidationError("Email requis.")
        
        email = email.strip().lower()
        
        if '@' not in email or '.' not in email:
            raise ValidationError("Format d'email invalide.")
        
        if len(email) < 5 or len(email) > 120:
            raise ValidationError("Email doit contenir entre 5 et 120 caractères.")
        
        return email
    
    @staticmethod
    def validate_username(username):
        """Validate username"""
        if not username or not username.strip():
            raise ValidationError("Nom d'utilisateur requis.")
        
        username = username.strip()
        
        if len(username) < 3 or len(username) > 80:
            raise ValidationError("Nom d'utilisateur doit contenir entre 3 et 80 caractères.")
        
        # Check for valid characters (alphanumeric, underscore, hyphen)
        if not all(c.isalnum() or c in ['_', '-'] for c in username):
            raise ValidationError("Nom d'utilisateur ne peut contenir que des lettres, chiffres, _ et -.")
        
        return username
    
    @staticmethod
    def validate_password(password):
        """Validate password strength"""
        if not password:
            raise ValidationError("Mot de passe requis.")
        
        if len(password) < 6:
            raise ValidationError("Mot de passe doit contenir au moins 6 caractères.")
        
        if len(password) > 100:
            raise ValidationError("Mot de passe trop long (max 100 caractères).")
        
        return password
    
    @staticmethod
    def validate_role(role):
        """Validate user role"""
        valid_roles = ['user', 'admin', 'invoicing', 'affecteur'] 
        
        if role not in valid_roles:
            raise ValidationError("Rôle invalide.")
        
        return role