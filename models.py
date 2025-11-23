from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """User model for authentication and file ownership"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')  # 'user', 'admin', 'invoicing', 'affecteur', 'évaluateur'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    files = db.relationship('File', foreign_keys='File.user_id', backref='owner', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if password matches hash"""
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        """Check if user is admin"""
        return self.role == 'admin'
    
    def __repr__(self):
        return f'<User {self.username}>'


class File(db.Model):
    """File model for tracking VOC files"""
    __tablename__ = 'files'
    
    id = db.Column(db.Integer, primary_key=True)
    file_number = db.Column(db.String(100), unique=True, nullable=False, index=True)
    receipt_date = db.Column(db.Date, nullable=False)
    importer = db.Column(db.String(200), nullable=False)
    exporter = db.Column(db.String(200), nullable=False)
    country = db.Column(db.String(100), nullable=False)
    
    # Route information
    route = db.Column(db.String(1), nullable=False)  # 'A', 'B', or 'C'
    sor_number = db.Column(db.String(100), nullable=True)  # Required for route B
    sol_number = db.Column(db.String(100), nullable=True)  # Required for route C
    
    # Status tracking
    status = db.Column(db.String(50), nullable=False, default='en attente d\'évaluation')
    # Possible statuses (in workflow order):
    # 1. en attente d'évaluation     - Initial state, waiting for evaluation
    # 2. en cours d'évaluation       - Being evaluated
    # 3. ready to invoice            - Ready for invoicing workflow
    # 4. payed                       - Invoice processed and paid
    # 5. en cours de traitement      - Under processing
    # 6. à compléter                 - Needs completion
    # 7. transfert à l'inspection    - Transferred to inspection
    # 8. Finalized                   - Final state, completed
    
    # Evaluation fields (Évaluateur)
    montant_facture = db.Column(db.Float, nullable=True)  # Amount entered by évaluateur
    evaluation_reason = db.Column(db.String(20), nullable=True)  # 'soumis', 'non_soumis', 'dispense'
    
    # Completion description
    completion_description = db.Column(db.Text, nullable=True)
    completion_date = db.Column(db.DateTime, nullable=True)
    
    # Recall management
    recall_date = db.Column(db.Date, nullable=True)
    
    # Invoicing fields
    mar_number = db.Column(db.String(100), nullable=True)
    proforma_number = db.Column(db.String(100), nullable=True)
    payment_justification_path = db.Column(db.String(500), nullable=True)
    invoiced_at = db.Column(db.DateTime, nullable=True)
    invoiced_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Relationships
    coc_details = db.relationship('CoCDetails', backref='file', uselist=False, cascade='all, delete-orphan')
    notifications = db.relationship('Notification', backref='file', lazy='dynamic', cascade='all, delete-orphan')
    invoicer = db.relationship('User', foreign_keys=[invoiced_by], backref='invoiced_files')
    
    def is_overdue(self):
        """Check if file has passed recall date"""
        if self.recall_date:
            return self.recall_date <= datetime.utcnow().date()
        return False
    
    def can_add_coc(self):
        """Check if CoC details can be added (status is Finalized)"""
        return self.status == 'Finalized'
    
    def can_be_invoiced(self):
        """Check if file is ready for invoicing"""
        return self.status == 'ready to invoice'
    
    def is_invoiced(self):
        """Check if file has been invoiced"""
        return self.status == 'payed' and self.mar_number and self.proforma_number
    
    def __repr__(self):
        return f'<File {self.file_number}>'


class CoCDetails(db.Model):
    """Certificate of Conformity details (only for finalized files)"""
    __tablename__ = 'coc_details'
    
    id = db.Column(db.Integer, primary_key=True)
    coc_date = db.Column(db.Date, nullable=False)
    coc_number = db.Column(db.String(100), nullable=False, unique=True)
    invoice_number = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign keys
    file_id = db.Column(db.Integer, db.ForeignKey('files.id'), nullable=False, unique=True)
    
    def __repr__(self):
        return f'<CoCDetails {self.coc_number}>'


class Notification(db.Model):
    """In-app notifications for users"""
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text, nullable=False)
    read_status = db.Column(db.Boolean, default=False)
    notification_type = db.Column(db.String(50), default='recall')  # 'recall', 'info', 'warning'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    file_id = db.Column(db.Integer, db.ForeignKey('files.id'), nullable=True)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('notifications', lazy='dynamic'))
    
    def __repr__(self):
        return f'<Notification {self.id} for User {self.user_id}>'

class StatusHistory(db.Model):
    """Track status changes for KPI calculations"""
    __tablename__ = 'status_history'
    
    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey('files.id'), nullable=False)
    old_status = db.Column(db.String(50), nullable=True)
    new_status = db.Column(db.String(50), nullable=False)
    changed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    changed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Relationships
    file = db.relationship('File', backref=db.backref('status_history', lazy='dynamic', cascade='all, delete-orphan'))
    user = db.relationship('User', backref='status_changes')
    
    def __repr__(self):
        return f'<StatusHistory {self.file_id}: {self.old_status} → {self.new_status}>'