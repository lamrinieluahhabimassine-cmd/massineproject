"""
Invoice routes: dashboard, invoice management
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, send_file
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime
from werkzeug.utils import secure_filename
from models import db, User, File, Notification
import os

invoice_bp = Blueprint('invoice', __name__, url_prefix='/invoice')

def invoicing_required(f):
    """Decorator to require invoicing role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(401)
        if current_user.role not in ['invoicing', 'admin']:
            flash('Accès réservé à l\'équipe de facturation.', 'danger')
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@invoice_bp.before_request
@login_required
@invoicing_required
def require_invoicing():
    """All invoice routes require invoicing role"""
    pass


@invoice_bp.route('/dashboard')
def dashboard():
    """Invoicing team dashboard"""
    # Get files ready for invoicing
    ready_files = File.query.filter_by(status='ready to invoice').order_by(File.updated_at.desc()).all()
    
    # Get files that have been invoiced (payed)
    invoiced_files = File.query.filter_by(status='payed').order_by(File.updated_at.desc()).limit(20).all()
    
    # Statistics
    stats = {
        'ready_to_invoice': len(ready_files),
        'invoiced_today': File.query.filter(
            File.status == 'payed',
            File.invoiced_at >= datetime.now().replace(hour=0, minute=0, second=0)
        ).count(),
        'total_invoiced': File.query.filter_by(status='payed').count(),
        'pending_my_action': len([f for f in ready_files if not f.invoiced_by])
    }
    
    return render_template('invoice/dashboard.html',
                         ready_files=ready_files,
                         invoiced_files=invoiced_files,
                         stats=stats)


@invoice_bp.route('/files/<int:file_id>')
def view_file(file_id):
    """View file details for invoicing"""
    file = File.query.get_or_404(file_id)
    
    # Invoicing team can view files that are ready or already invoiced
    if file.status not in ['ready to invoice', 'payed']:
        flash('Ce dossier n\'est pas dans la phase de facturation.', 'warning')
        return redirect(url_for('invoice.dashboard'))
    
    return render_template('invoice/file_detail.html', file=file)


@invoice_bp.route('/files/<int:file_id>/process', methods=['GET', 'POST'])
def process_invoice(file_id):
    """Process invoice for a file"""
    file = File.query.get_or_404(file_id)
    
    # Check if file is ready to invoice
    if not file.can_be_invoiced():
        flash('Ce dossier ne peut pas être facturé actuellement.', 'danger')
        return redirect(url_for('invoice.dashboard'))
    
    # Check if already invoiced
    if file.is_invoiced():
        flash('Ce dossier a déjà été facturé.', 'info')
        return redirect(url_for('invoice.view_file', file_id=file.id))
    
    if request.method == 'POST':
        # Get form data
        mar_number = request.form.get('mar_number', '').strip()
        proforma_number = request.form.get('proforma_number', '').strip()
        payment_file = request.files.get('payment_justification')
        
        # Validate
        errors = []
        
        if not mar_number:
            errors.append('Numéro MAR requis.')
        elif len(mar_number) < 3 or len(mar_number) > 100:
            errors.append('Numéro MAR invalide (3-100 caractères).')
        
        if not proforma_number:
            errors.append('Numéro ProForma requis.')
        elif len(proforma_number) < 3 or len(proforma_number) > 100:
            errors.append('Numéro ProForma invalide (3-100 caractères).')
        
        if not payment_file or payment_file.filename == '':
            errors.append('Justificatif de paiement requis.')
        else:
            # Check file extension
            allowed_extensions = {'pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png'}
            filename = payment_file.filename.lower()
            if '.' not in filename or filename.rsplit('.', 1)[1] not in allowed_extensions:
                errors.append('Format de fichier non autorisé (PDF, DOC, DOCX, JPG, PNG uniquement).')
        
        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('invoice/process_form.html', file=file)
        
        try:
            # Create uploads directory if it doesn't exist
            upload_folder = os.path.join('uploads', 'payments')
            os.makedirs(upload_folder, exist_ok=True)
            
            # Generate unique filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            original_filename = secure_filename(payment_file.filename)
            name, ext = os.path.splitext(original_filename)
            filename = f"{file.file_number}_{timestamp}{ext}"
            file_path = os.path.join(upload_folder, filename)
            
            # Save file
            payment_file.save(file_path)
            
            # Update file record
            file.mar_number = mar_number.upper()
            file.proforma_number = proforma_number.upper()
            file.payment_justification_path = file_path
            file.status = 'payed'
            file.invoiced_at = datetime.utcnow()
            file.invoiced_by = current_user.id
            
            db.session.commit()
            
            # Create notification for file owner
            notification = Notification(
                message=f"✅ Facturation terminée pour le dossier {file.file_number}. Numéro MAR: {file.mar_number}, ProForma: {file.proforma_number}",
                user_id=file.user_id,
                file_id=file.id,
                notification_type='info',
                read_status=False
            )
            db.session.add(notification)
            
            # Also notify admins
            admins = User.query.filter_by(role='admin').all()
            for admin in admins:
                admin_notif = Notification(
                    message=f"📋 Dossier {file.file_number} facturé par {current_user.username}",
                    user_id=admin.id,
                    file_id=file.id,
                    notification_type='info',
                    read_status=False
                )
                db.session.add(admin_notif)
            
            db.session.commit()
            
            # Send email notification (optional - will work if email is configured)
            try:
                from utils.email import send_invoice_completed_notification
                send_invoice_completed_notification(file, file.owner, current_user)
            except:
                pass  # Email not configured or function not available
            
            flash(f'✅ Dossier {file.file_number} facturé avec succès!', 'success')
            return redirect(url_for('invoice.dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'❌ Erreur lors du traitement: {str(e)}', 'danger')
            return render_template('invoice/process_form.html', file=file)
    
    return render_template('invoice/process_form.html', file=file)


@invoice_bp.route('/files/<int:file_id>/payment-justification')
def download_payment_justification(file_id):
    """Download payment justification file"""
    file = File.query.get_or_404(file_id)
    
    if not file.payment_justification_path or not os.path.exists(file.payment_justification_path):
        flash('Fichier non trouvé.', 'danger')
        return redirect(url_for('invoice.view_file', file_id=file.id))
    
    return send_file(file.payment_justification_path, as_attachment=True)


@invoice_bp.route('/files/ready')
def ready_files():
    """View all files ready to invoice"""
    files = File.query.filter_by(status='ready to invoice').order_by(File.updated_at.desc()).all()
    
    return render_template('invoice/ready_files.html', files=files)


@invoice_bp.route('/files/invoiced')
def invoiced_files():
    """View all invoiced files"""
    files = File.query.filter_by(status='payed').order_by(File.invoiced_at.desc()).all()
    
    return render_template('invoice/invoiced_files.html', files=files)