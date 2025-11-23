from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from functools import wraps
from datetime import date, datetime
from models import db, User, File, CoCDetails, Notification
from utils.validation import Validator
from models import StatusHistory

user_bp = Blueprint('user', __name__, url_prefix='/user')

def user_required(f):
    """Decorator to require user or admin role (block invoicing team)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(401)
        if current_user.role == 'invoicing':
            flash('⛔ Accès non autorisé. Vous êtes dans l\'équipe de facturation.', 'danger')
            return redirect(url_for('invoice.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@user_bp.before_request
@login_required
@user_required
def require_user():
    """All user routes require user or admin login (not invoicing)"""
    pass


@user_bp.route('/dashboard')
def dashboard():
    """User dashboard - view own files (payed and after only)"""
    # Get files that are "payed" and after (payed, en cours de traitement, à compléter, transfert à l'inspection, Finalized)
    allowed_statuses = ['payed', 'en cours de traitement', 'à compléter', 'transfert à l\'inspection', 'Finalized']
    
    files = File.query.filter(
        File.user_id == current_user.id,
        File.status.in_(allowed_statuses)
    ).order_by(File.created_at.desc()).all()
    
    # Get unassigned "payed" files for self-assignment dropdown
    unassigned_payed_files = File.query.filter(
        File.status == 'payed',
        File.user_id == None  # Not assigned to anyone
    ).order_by(File.file_number).all()
    
    # Get statistics
    today = date.today()
    stats = {
        'total': len(files),
        'payed': len([f for f in files if f.status == 'payed']),
        'in_progress': len([f for f in files if f.status == 'en cours de traitement']),
        'completion': len([f for f in files if f.status == 'à compléter']),
        'finalized': len([f for f in files if f.status == 'Finalized']),
        'overdue': len([f for f in files if f.recall_date and f.recall_date <= today and f.status != 'Finalized'])
    }
    
    # Get overdue files
    overdue_files = [f for f in files if f.recall_date and f.recall_date <= today and f.status != 'Finalized']
    
    return render_template('user/dashboard.html', 
                         files=files, 
                         unassigned_payed_files=unassigned_payed_files,
                         stats=stats, 
                         overdue_files=overdue_files,
                         today=today)

@user_bp.route('/files/new', methods=['GET', 'POST'])
def new_file():
    """Create new file"""
    if request.method == 'POST':
        # Get form data
        file_number = request.form.get('file_number', '').strip()
        receipt_date_str = request.form.get('receipt_date', '').strip()
        importer = request.form.get('importer', '').strip()
        exporter = request.form.get('exporter', '').strip()
        country = request.form.get('country', '').strip()
        route = request.form.get('route', '').strip()
        sor_number = request.form.get('sor_number', '').strip()
        sol_number = request.form.get('sol_number', '').strip()
        status = request.form.get('status', '').strip()
        recall_date_str = request.form.get('recall_date', '').strip()
        
        # Validate
        try:
            Validator.validate_file_number(file_number)
            Validator.validate_date_string(receipt_date_str, 'receipt_date')
            Validator.validate_non_empty(importer, 'Importateur')
            Validator.validate_non_empty(exporter, 'Exportateur')
            Validator.validate_non_empty(country, 'Pays')
            Validator.validate_route(route, sor_number, sol_number)
            Validator.validate_status(status)
            
            # Parse dates
            receipt_date = datetime.strptime(receipt_date_str, '%Y-%m-%d').date()
            recall_date = None
            if recall_date_str:
                recall_date = datetime.strptime(recall_date_str, '%Y-%m-%d').date()
                Validator.validate_recall_date(recall_date)
            
            # Check if file number already exists
            if File.query.filter_by(file_number=file_number).first():
                flash('Ce numéro de dossier existe déjà.', 'danger')
                return render_template('user/file_form.html', edit=False)
            
            # Create new file
            new_file = File(
                file_number=file_number,
                receipt_date=receipt_date,
                importer=importer,
                exporter=exporter,
                country=country,
                route=route,
                sor_number=sor_number if route == 'B' else None,
                sol_number=sol_number if route == 'C' else None,
                status=status,
                recall_date=recall_date,
                user_id=current_user.id
            )
            
            db.session.add(new_file)
            db.session.commit()
            
            flash(f'Dossier {file_number} créé avec succès!', 'success')
            return redirect(url_for('user.view_file', file_id=new_file.id))
            
        except Exception as e:
            flash(str(e), 'danger')
            return render_template('user/file_form.html', edit=False)
    
    return render_template('user/file_form.html', edit=False)


@user_bp.route('/files/<int:file_id>')
def view_file(file_id):
    """View file details"""
    file = File.query.get_or_404(file_id)
    
    # Check if user owns this file
    if file.user_id != current_user.id and not current_user.is_admin():
        flash('Vous n\'avez pas accès à ce dossier.', 'danger')
        return redirect(url_for('user.dashboard'))
    
    return render_template('user/file_detail.html', file=file)


@user_bp.route('/files/<int:file_id>/edit', methods=['GET', 'POST'])
def edit_file(file_id):
    """Edit file"""
    file = File.query.get_or_404(file_id)
    
    # Check if user owns this file
    if file.user_id != current_user.id and not current_user.is_admin():
        flash('Vous n\'avez pas accès à ce dossier.', 'danger')
        return redirect(url_for('user.dashboard'))
    
    if request.method == 'POST':
        # Get form data
        receipt_date_str = request.form.get('receipt_date', '').strip()
        importer = request.form.get('importer', '').strip()
        exporter = request.form.get('exporter', '').strip()
        country = request.form.get('country', '').strip()
        route = request.form.get('route', '').strip()
        sor_number = request.form.get('sor_number', '').strip()
        sol_number = request.form.get('sol_number', '').strip()
        status = request.form.get('status', '').strip()
        recall_date_str = request.form.get('recall_date', '').strip()
        completion_description = request.form.get('completion_description', '').strip()
        
        # Validate
        try:
            Validator.validate_date_string(receipt_date_str, 'receipt_date')
            Validator.validate_non_empty(importer, 'Importateur')
            Validator.validate_non_empty(exporter, 'Exportateur')
            Validator.validate_non_empty(country, 'Pays')
            Validator.validate_route(route, sor_number, sol_number)
            Validator.validate_status(status)
            
            # If status is "à compléter", require description
            if status == 'à compléter' and not completion_description:
                flash('La description est obligatoire pour le statut "À Compléter".', 'danger')
                return render_template('user/file_form.html', file=file, edit=True)
            
            # Parse dates
            receipt_date = datetime.strptime(receipt_date_str, '%Y-%m-%d').date()
            recall_date = None
            if recall_date_str:
                recall_date = datetime.strptime(recall_date_str, '%Y-%m-%d').date()
                Validator.validate_recall_date(recall_date)
            
            # ✅ TRACK STATUS CHANGE
            old_status = file.status
            
            # Update file
            file.receipt_date = receipt_date
            file.importer = importer
            file.exporter = exporter
            file.country = country
            file.route = route
            file.sor_number = sor_number if route == 'B' else None
            file.sol_number = sol_number if route == 'C' else None
            file.status = status
            file.recall_date = recall_date
            
            # Update completion fields if status is "à compléter"
            if status == 'à compléter':
                file.completion_description = completion_description
                file.completion_date = datetime.utcnow()
            
            db.session.commit()
            
            # ✅ ADD STATUS HISTORY ENTRY IF STATUS CHANGED
            if old_status != status:
                from models import StatusHistory
                history = StatusHistory(
                    file_id=file.id,
                    old_status=old_status,
                    new_status=status,
                    changed_at=datetime.utcnow(),
                    changed_by=current_user.id
                )
                db.session.add(history)
                db.session.commit()
            
            # If status changed to "ready to invoice", notify invoicing team
            if status == 'ready to invoice' and old_status != 'ready to invoice':
                # Create notifications for invoicing team
                invoicing_users = User.query.filter_by(role='invoicing').all()
                for inv_user in invoicing_users:
                    notification = Notification(
                        message=f"📋 Nouveau dossier prêt à facturer: {file.file_number} par {current_user.username}",
                        user_id=inv_user.id,
                        file_id=file.id,
                        notification_type='info',
                        read_status=False
                    )
                    db.session.add(notification)
                db.session.commit()
            
            flash('Dossier mis à jour avec succès!', 'success')
            return redirect(url_for('user.view_file', file_id=file.id))
            
        except Exception as e:
            flash(str(e), 'danger')
            return render_template('user/file_form.html', file=file, edit=True)

            
        except Exception as e:
            flash(str(e), 'danger')
            return render_template('user/file_form.html', file=file, edit=True)
    
    return render_template('user/file_form.html', file=file, edit=True)


@user_bp.route('/files/<int:file_id>/delete', methods=['POST'])
def delete_file(file_id):
    """Delete file"""
    file = File.query.get_or_404(file_id)
    
    # Check if user owns this file
    if file.user_id != current_user.id and not current_user.is_admin():
        flash('Vous n\'avez pas accès à ce dossier.', 'danger')
        return redirect(url_for('user.dashboard'))
    
    file_number = file.file_number
    db.session.delete(file)
    db.session.commit()
    
    flash(f'Dossier {file_number} supprimé avec succès.', 'success')
    return redirect(url_for('user.dashboard'))


@user_bp.route('/files/<int:file_id>/add-coc', methods=['GET', 'POST'])
def add_coc(file_id):
    """Add Certificate of Conformity details"""
    file = File.query.get_or_404(file_id)
    
    # Check if user owns this file
    if file.user_id != current_user.id and not current_user.is_admin():
        flash('Vous n\'avez pas accès à ce dossier.', 'danger')
        return redirect(url_for('user.dashboard'))
    
    # Check if file is finalized
    if not file.can_add_coc():
        flash('Le CoC ne peut être ajouté qu\'aux dossiers finalisés.', 'danger')
        return redirect(url_for('user.view_file', file_id=file.id))
    
    # Check if CoC already exists
    if file.coc_details:
        flash('Ce dossier a déjà un CoC.', 'info')
        return redirect(url_for('user.view_file', file_id=file.id))
    
    if request.method == 'POST':
        # Get form data
        coc_date_str = request.form.get('coc_date', '').strip()
        coc_number = request.form.get('coc_number', '').strip()
        invoice_number = request.form.get('invoice_number', '').strip()
        
        # Validate
        try:
            Validator.validate_date_string(coc_date_str, 'coc_date')
            Validator.validate_non_empty(coc_number, 'Numéro CoC')
            Validator.validate_non_empty(invoice_number, 'Numéro de facture')
            
            # Parse date
            coc_date = datetime.strptime(coc_date_str, '%Y-%m-%d').date()
            
            # Check if CoC number already exists
            if CoCDetails.query.filter_by(coc_number=coc_number).first():
                flash('Ce numéro de CoC existe déjà.', 'danger')
                return render_template('user/coc_form.html', file=file)
            
            # Create CoC
            coc = CoCDetails(
                coc_date=coc_date,
                coc_number=coc_number,
                invoice_number=invoice_number,
                file_id=file.id
            )
            
            db.session.add(coc)
            db.session.commit()
            
            flash(f'CoC {coc_number} ajouté avec succès!', 'success')
            return redirect(url_for('user.view_file', file_id=file.id))
            
        except Exception as e:
            flash(str(e), 'danger')
            return render_template('user/coc_form.html', file=file)
    
    return render_template('user/coc_form.html', file=file)

@user_bp.route('/file/<int:file_id>/set-completion', methods=['POST'])
@login_required
def set_completion(file_id):
    """Set file status to 'à compléter' with description"""
    file = File.query.get_or_404(file_id)
    
    # Check ownership
    if file.user_id != current_user.id and not current_user.is_admin():
        flash('Accès refusé.', 'danger')
        return redirect(url_for('user.dashboard'))
    
    description = request.form.get('completion_description', '').strip()
    
    if not description:
        flash('La description ne peut pas être vide.', 'danger')
        return redirect(url_for('user.view_file', file_id=file_id))
    
    try:
        old_status = file.status
        
        # Update file status and description
        file.status = 'à compléter'
        file.completion_description = description
        file.completion_date = datetime.utcnow()
        
        # Record status change
        status_history = StatusHistory(
            file_id=file.id,
            old_status=old_status,
            new_status='à compléter',
            changed_by=current_user.id
        )
        
        db.session.add(status_history)
        db.session.commit()
        
        flash('✅ Dossier marqué à compléter avec description.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'❌ Erreur: {str(e)}', 'danger')
    
    return redirect(url_for('user.view_file', file_id=file_id))

@user_bp.route('/files/self-assign/<int:file_id>', methods=['POST'])
@login_required
def self_assign_file(file_id):
    """Self-assign a payed file and change status to en cours de traitement"""
    file = File.query.get_or_404(file_id)
    
    # Check if file is "payed" and unassigned
    if file.status != 'payed':
        flash('Ce dossier n\'est pas dans le statut "Payed".', 'danger')
        return redirect(url_for('user.dashboard'))
    
    if file.user_id is not None:
        flash('Ce dossier est déjà affecté à quelqu\'un.', 'danger')
        return redirect(url_for('user.dashboard'))
    
    try:
        # Assign to current user
        file.user_id = current_user.id
        
        # Change status to "en cours de traitement"
        old_status = file.status
        file.status = 'en cours de traitement'
        
        db.session.commit()
        
        # Record status change
        history = StatusHistory(
            file_id=file.id,
            old_status=old_status,
            new_status='en cours de traitement',
            changed_at=datetime.utcnow(),
            changed_by=current_user.id
        )
        db.session.add(history)
        db.session.commit()
        
        flash(f'✅ Dossier {file.file_number} affecté à vous avec succès! Status: En cours de traitement', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'❌ Erreur: {str(e)}', 'danger')
    
    return redirect(url_for('user.dashboard'))