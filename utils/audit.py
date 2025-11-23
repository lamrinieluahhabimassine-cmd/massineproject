"""
Audit logging system for tracking user actions
"""
from datetime import datetime
from flask_login import current_user
from flask import request
from models import db
import logging

logger = logging.getLogger(__name__)

class AuditLog(db.Model):
    """Audit log model for tracking all important actions"""
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(100), nullable=False, index=True)
    resource_type = db.Column(db.String(50), nullable=True)  # 'file', 'user', etc.
    resource_id = db.Column(db.Integer, nullable=True)
    details = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(200), nullable=True)
    
    user = db.relationship('User', backref=db.backref('audit_logs', lazy='dynamic'))
    
    def __repr__(self):
        return f'<AuditLog {self.action} by User {self.user_id}>'


def log_action(action, resource_type=None, resource_id=None, details=None):
    """
    Log an action to the audit trail
    
    Args:
        action: Action performed (e.g., 'create_file', 'update_status', 'login')
        resource_type: Type of resource affected ('file', 'user', etc.)
        resource_id: ID of the resource
        details: Additional details (JSON string or text)
    """
    try:
        from flask import request
        
        audit = AuditLog(
            user_id=current_user.id if current_user.is_authenticated else None,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=request.remote_addr if request else None,
            user_agent=request.headers.get('User-Agent', '')[:200] if request else None
        )
        
        db.session.add(audit)
        db.session.commit()
        
        logger.info(f"Audit: {action} by user {current_user.id if current_user.is_authenticated else 'anonymous'}")
        
    except Exception as e:
        logger.error(f"Failed to log audit action: {e}")
        db.session.rollback()


def log_file_action(action, file, details=None):
    """Helper to log file-related actions"""
    log_action(
        action=action,
        resource_type='file',
        resource_id=file.id,
        details=details or f"File: {file.file_number}"
    )


def log_user_action(action, user, details=None):
    """Helper to log user-related actions"""
    log_action(
        action=action,
        resource_type='user',
        resource_id=user.id,
        details=details or f"User: {user.username}"
    )


def log_auth_action(action, username=None, success=True):
    """Helper to log authentication actions"""
    details = f"Username: {username}, Success: {success}"
    log_action(
        action=action,
        resource_type='auth',
        details=details
    )


def get_user_activity(user_id, limit=50):
    """Get recent activity for a specific user"""
    return AuditLog.query.filter_by(user_id=user_id)\
        .order_by(AuditLog.timestamp.desc())\
        .limit(limit).all()


def get_file_history(file_id, limit=50):
    """Get all actions related to a specific file"""
    return AuditLog.query.filter_by(
        resource_type='file',
        resource_id=file_id
    ).order_by(AuditLog.timestamp.desc()).limit(limit).all()


def get_recent_activity(limit=100):
    """Get recent activity across the platform (admin view)"""
    return AuditLog.query\
        .order_by(AuditLog.timestamp.desc())\
        .limit(limit).all()


# Common action constants
ACTION_LOGIN = 'login'
ACTION_LOGOUT = 'logout'
ACTION_FAILED_LOGIN = 'failed_login'
ACTION_CREATE_FILE = 'create_file'
ACTION_UPDATE_FILE = 'update_file'
ACTION_DELETE_FILE = 'delete_file'
ACTION_ADD_COC = 'add_coc'
ACTION_STATUS_CHANGE = 'status_change'
ACTION_CREATE_USER = 'create_user'
ACTION_UPDATE_USER = 'update_user'
ACTION_DISABLE_USER = 'disable_user'
ACTION_CHANGE_ROLE = 'change_role'
ACTION_EXPORT_DATA = 'export_data'
ACTION_SEND_RECALL = 'send_recall'