"""
File upload and attachment management
"""
import os
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import current_app
from models import db

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'png', 'jpg', 'jpeg'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

class FileAttachment(db.Model):
    """Model for file attachments"""
    __tablename__ = 'file_attachments'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)  # in bytes
    mime_type = db.Column(db.String(100), nullable=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign keys
    file_id = db.Column(db.Integer, db.ForeignKey('files.id'), nullable=False)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationships
    file = db.relationship('File', backref=db.backref('attachments', lazy='dynamic', cascade='all, delete-orphan'))
    uploader = db.relationship('User', backref=db.backref('uploads', lazy='dynamic'))
    
    def __repr__(self):
        return f'<FileAttachment {self.original_filename}>'
    
    @property
    def human_readable_size(self):
        """Convert bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if self.file_size < 1024.0:
                return f"{self.file_size:.1f} {unit}"
            self.file_size /= 1024.0
        return f"{self.file_size:.1f} TB"


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_upload_folder():
    """Get the upload folder path"""
    upload_folder = os.path.join(current_app.root_path, 'uploads')
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    return upload_folder


def generate_unique_filename(original_filename):
    """Generate a unique filename to prevent conflicts"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    name, ext = os.path.splitext(secure_filename(original_filename))
    return f"{name}_{timestamp}{ext}"


def save_file(file, file_id, user_id):
    """
    Save uploaded file
    
    Args:
        file: FileStorage object from request.files
        file_id: ID of the associated File record
        user_id: ID of the user uploading
        
    Returns:
        FileAttachment object or None if failed
    """
    if not file or file.filename == '':
        return None, "Aucun fichier sélectionné"
    
    if not allowed_file(file.filename):
        return None, f"Type de fichier non autorisé. Extensions autorisées: {', '.join(ALLOWED_EXTENSIONS)}"
    
    # Check file size
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    if file_size > MAX_FILE_SIZE:
        return None, f"Fichier trop volumineux. Taille maximale: {MAX_FILE_SIZE / (1024*1024):.0f}MB"
    
    try:
        # Generate unique filename
        filename = generate_unique_filename(file.filename)
        
        # Save file
        upload_folder = get_upload_folder()
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)
        
        # Create database record
        attachment = FileAttachment(
            filename=filename,
            original_filename=file.filename,
            file_path=file_path,
            file_size=file_size,
            mime_type=file.content_type,
            file_id=file_id,
            uploaded_by=user_id
        )
        
        db.session.add(attachment)
        db.session.commit()
        
        return attachment, None
        
    except Exception as e:
        db.session.rollback()
        # Clean up file if database save failed
        if os.path.exists(file_path):
            os.remove(file_path)
        return None, f"Erreur lors du téléchargement: {str(e)}"


def delete_file(attachment_id):
    """Delete a file attachment"""
    attachment = FileAttachment.query.get(attachment_id)
    if not attachment:
        return False, "Fichier non trouvé"
    
    try:
        # Delete physical file
        if os.path.exists(attachment.file_path):
            os.remove(attachment.file_path)
        
        # Delete database record
        db.session.delete(attachment)
        db.session.commit()
        
        return True, "Fichier supprimé avec succès"
        
    except Exception as e:
        db.session.rollback()
        return False, f"Erreur lors de la suppression: {str(e)}"


def get_file_attachments(file_id):
    """Get all attachments for a file"""
    return FileAttachment.query.filter_by(file_id=file_id)\
        .order_by(FileAttachment.uploaded_at.desc()).all()