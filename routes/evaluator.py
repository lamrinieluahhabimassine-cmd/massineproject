"""
Evaluator routes: evaluate files and set evaluation decision
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime
from models import db, File, Notification, StatusHistory, User

evaluator_bp = Blueprint('evaluator', __name__, url_prefix='/evaluator')

def evaluator_required(f):
    """Decorator to require evaluator role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(401)
        if current_user.role not in ['évaluateur', 'admin']:
            flash('Accès réservé aux évaluateurs.', 'danger')
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@evaluator_bp.before_request
@login_required
@evaluator_required
def require_evaluator():
    """All evaluator routes require evaluator role"""
    pass


@evaluator_bp.route('/dashboard')
def dashboard():
    """Evaluator dashboard - files waiting for evaluation"""
    # Get files that are "en attente d'évaluation" and NOT assigned to anyone
    pending_files = File.query.filter(
        File.status == 'en attente d\'évaluation',
        File.user_id == None
    ).order_by(File.created_at.desc()).all()
    
    # Get files that are "en attente d'évaluation" and assigned to current user
    in_progress_files = File.query.filter(
        File.status == 'en attente d\'évaluation',
        File.user_id == current_user.id
    ).order_by(File.created_at.desc()).all()
    
    stats = {
        'pending': len(pending_files),
        'in_progress': len(in_progress_files),
    }
    
    return render_template('evaluator/dashboard.html',
                         pending_files=pending_files,
                         in_progress_files=in_progress_files,
                         stats=stats)


@evaluator_bp.route('/files/<int:file_id>/start-evaluation', methods=['POST'])
def start_evaluation(file_id):
    """Start evaluating a file (change status to 'en cours d\'évaluation')"""
    file = File.query.get_or_404(file_id)
    
    # Check if file is in pending status
    if file.status != 'en attente d\'évaluation':
        flash('Ce dossier n\'est pas en attente d\'évaluation.', 'danger')
        return redirect(url_for('evaluator.dashboard'))
    
    try:
        file.status = 'en cours d\'évaluation'
        
        # Record status change
        history = StatusHistory(
            file_id=file.id,
            old_status='en attente d\'évaluation',
            new_status='en cours d\'évaluation',
            changed_at=datetime.utcnow(),
            changed_by=current_user.id
        )
        
        db.session.add(history)
        db.session.commit()
        
        flash('✅ Vous avez commencé l\'évaluation de ce dossier.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'❌ Erreur: {str(e)}', 'danger')
    
    return redirect(url_for('evaluator.evaluate_file', file_id=file_id))


@evaluator_bp.route('/files/<int:file_id>/evaluate', methods=['GET', 'POST'])
def evaluate_file(file_id):
    """Evaluate a file with decision and amount"""
    file = File.query.get_or_404(file_id)
    
    # Check if file is in pending status and assigned to current user
    if file.status != 'en attente d\'évaluation':
        flash('Ce dossier n\'est pas en attente d\'évaluation.', 'danger')
        return redirect(url_for('evaluator.dashboard'))

    if file.user_id != current_user.id:
        flash('Ce dossier n\'est pas assigné à vous.', 'danger')
        return redirect(url_for('evaluator.dashboard'))
    
    if request.method == 'POST':
        montant_facture_str = request.form.get('montant_facture', '').strip()
        decision = request.form.get('decision', '').strip()
        
        # Validate decision first
        if not decision or decision not in ['soumis', 'non_soumis', 'dispense']:
            flash('Vous devez choisir une décision.', 'danger')
            return render_template('evaluator/evaluate_form.html', file=file)
        
        # Validate montant only if decision is "soumis"
        if decision == 'soumis' and not montant_facture_str:
            flash('Le montant de facture est obligatoire pour la décision "Soumis".', 'danger')
            return render_template('evaluator/evaluate_form.html', file=file)
        
        # Only validate and convert montant if decision is "soumis"
        montant_facture = None
        if decision == 'soumis':
            try:
                montant_facture = float(montant_facture_str)
                if montant_facture < 0:
                    raise ValueError("Le montant doit être positif")
            except ValueError:
                flash('Le montant doit être un nombre valide.', 'danger')
                return render_template('evaluator/evaluate_form.html', file=file)
        
        try:
            # Save decision
            file.evaluation_reason = decision
            
            # Save montant only if decision is "soumis"
            if decision == 'soumis':
                file.montant_facture = montant_facture
            else:
                file.montant_facture = None
            
            # Determine new status based on decision
            if decision == 'soumis':
                new_status = 'ready to invoice'
            else:  # non_soumis or dispense
                new_status = 'Finalized'
            
            old_status = file.status
            file.status = new_status
            
            db.session.commit()
            
            # Record status change
            history = StatusHistory(
                file_id=file.id,
                old_status=old_status,
                new_status=new_status,
                changed_at=datetime.utcnow(),
                changed_by=current_user.id
            )
            db.session.add(history)
            
            # If status is "ready to invoice", notify invoicing team
            if new_status == 'ready to invoice':
                invoicing_users = User.query.filter_by(role='invoicing').all()
                for inv_user in invoicing_users:
                    notification = Notification(
                        message=f"💰 Nouveau dossier prêt à facturer: {file.file_number} (Montant: {montant_facture})",
                        user_id=inv_user.id,
                        file_id=file.id,
                        notification_type='info',
                        read_status=False
                    )
                    db.session.add(notification)
            
            db.session.commit()
            
            decision_text = 'Soumis' if decision == 'soumis' else ('Non soumis' if decision == 'non_soumis' else 'Dispensé')
            flash(f'✅ Dossier évalué comme "{decision_text}"', 'success')
            
            return redirect(url_for('evaluator.dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'❌ Erreur: {str(e)}', 'danger')
            return render_template('evaluator/evaluate_form.html', file=file)
    
    return render_template('evaluator/evaluate_form.html', file=file)


@evaluator_bp.route('/files/batch-assign/<int:count>', methods=['POST'])
@login_required
def batch_assign_files(count):
    """Batch assign up to 'count' unassigned files to current evaluator"""
    
    # Validate count
    if count < 1 or count > 10:
        flash('Le nombre de dossiers doit être entre 1 et 10.', 'danger')
        return redirect(url_for('evaluator.dashboard'))
    
    try:
        # Get unassigned files waiting for evaluation
        unassigned_files = File.query.filter(
            File.status == 'en attente d\'évaluation',
            File.user_id == None
        ).order_by(File.created_at).limit(count).all()
        
        if not unassigned_files:
            flash('Aucun dossier en attente d\'évaluation disponible.', 'warning')
            return redirect(url_for('evaluator.dashboard'))
        
        assigned_count = len(unassigned_files)
        
        # Assign files to current evaluator
        for file in unassigned_files:
            file.user_id = current_user.id
            # Status stays as "en attente d'évaluation"
            db.session.add(file)
        
        db.session.commit()
        
        flash(f'✅ {assigned_count} dossier(s) affecté(s) à vous pour évaluation!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'❌ Erreur: {str(e)}', 'danger')
    
    return redirect(url_for('evaluator.dashboard'))