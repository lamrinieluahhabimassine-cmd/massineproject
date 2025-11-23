"""
Admin routes: dashboard, user management, file oversight
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from functools import wraps
from datetime import date
from models import db, User, File, CoCDetails, Notification

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('Accès réservé aux administrateurs.', 'danger')
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.before_request
@login_required
@admin_required
def require_admin():
    """All admin routes require admin login"""
    pass

@admin_bp.route('/dashboard')
def dashboard():
    """Admin dashboard - overview of all files and users"""
    # Get all files
    all_files = File.query.order_by(File.created_at.desc()).all()
    
    # Get files with alerts (overdue recall_date)
    today = date.today()
    alert_files = [f for f in all_files if f.recall_date and f.recall_date <= today and f.status != 'Finalized']
    
    # Get all users
    all_users = User.query.order_by(User.created_at.desc()).all()
    
    # Statistics
    stats = {
        'total_files': len(all_files),
        'total_users': len(all_users),
        'pending': len([f for f in all_files if f.status == 'en attente d\'évaluation']),
        'in_progress': len([f for f in all_files if f.status in ['en cours d\'évaluation', 'ready to invoice', 'payed', 'en cours de traitement', 'transfert à l\'inspection']]),
        'finalized': len([f for f in all_files if f.status == 'Finalized']),
        'alerts': len(alert_files),
        'route_a': len([f for f in all_files if f.route == 'A']),
        'route_b': len([f for f in all_files if f.route == 'B']),
        'route_c': len([f for f in all_files if f.route == 'C']),
        # ✅ NEW - Invoice statistics
        'ready_to_invoice': len([f for f in all_files if f.status == 'ready to invoice']),
        'invoiced': len([f for f in all_files if f.status == 'payed']),
    }
    
    return render_template('admin/dashboard.html', 
                         files=all_files[:10],  # Show recent 10 files
                         alert_files=alert_files,
                         users=all_users,
                         stats=stats)


@admin_bp.route('/files')
def files():
    """View all files"""
    # Get filter parameters
    status_filter = request.args.get('status', '')
    route_filter = request.args.get('route', '')
    user_filter = request.args.get('user', '')
    
    # Base query
    query = File.query
    
    # Apply filters
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    if route_filter:
        query = query.filter_by(route=route_filter)
    
    if user_filter:
        query = query.filter_by(user_id=int(user_filter))
    
    files = query.order_by(File.created_at.desc()).all()
    
    # Get all users for filter dropdown
    users = User.query.all()
    
    return render_template('admin/files.html', 
                         files=files,
                         users=users,
                         status_filter=status_filter,
                         route_filter=route_filter,
                         user_filter=user_filter)


@admin_bp.route('/users')
def users():
    """View all users"""
    users = User.query.order_by(User.created_at.desc()).all()
    
    # Get file counts per user
    user_stats = {}
    for user in users:
        user_stats[user.id] = {
            'total_files': File.query.filter_by(user_id=user.id).count(),
            'finalized': File.query.filter_by(user_id=user.id, status='Finalized').count()
        }
    
    return render_template('admin/users.html', users=users, user_stats=user_stats)


@admin_bp.route('/users/<int:user_id>/toggle-status')
def toggle_user_status(user_id):
    """Activate/deactivate user"""
    user = User.query.get_or_404(user_id)
    
    # Prevent admin from deactivating themselves
    if user.id == current_user.id:
        flash('Vous ne pouvez pas désactiver votre propre compte.', 'warning')
        return redirect(url_for('admin.users'))
    
    user.is_active = not user.is_active
    db.session.commit()
    
    status = "activé" if user.is_active else "désactivé"
    flash(f'Utilisateur {user.username} {status}.', 'success')
    
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/<int:user_id>/toggle-role')
def toggle_user_role(user_id):
    """Toggle user between user and admin role (LEGACY - Use set_user_role instead)"""
    user = User.query.get_or_404(user_id)
    
    # Prevent admin from changing their own role
    if user.id == current_user.id:
        flash('Vous ne pouvez pas modifier votre propre rôle.', 'warning')
        return redirect(url_for('admin.users'))
    
    user.role = 'user' if user.role == 'admin' else 'admin'
    db.session.commit()
    
    flash(f'Rôle de {user.username} changé en {user.role}.', 'success')
    
    return redirect(url_for('admin.users'))



@admin_bp.route('/users/<int:user_id>/set-role/<role>')
def set_user_role(user_id, role):
    """Set user to specific role"""
    user = User.query.get_or_404(user_id)
    
    # Prevent admin from changing their own role
    if user.id == current_user.id:
        flash('Vous ne pouvez pas modifier votre propre rôle.', 'warning')
        return redirect(url_for('admin.users'))
    
    # Validate role
    valid_roles = ['user', 'admin', 'invoicing', 'affecteur', 'évaluateur']
    if role not in valid_roles:
        flash('Rôle invalide.', 'danger')
        return redirect(url_for('admin.users'))
    
    old_role = user.role
    user.role = role
    db.session.commit()
    
    # Log action (if audit system is enabled)
    try:
        from utils.audit import log_user_action
        log_user_action('change_role', user, details=f"Role changed from {old_role} to {role}")
    except ImportError:
        pass  # Audit system not available yet
    
    # Display role name in French
    role_names = {
    'user': 'Utilisateur',
    'admin': 'Administrateur',
    'invoicing': 'Facturation',
    'affecteur': 'Affecteur',
    'évaluateur': 'Évaluateur'
}
    
    flash(f'Rôle de {user.username} changé en {role_names.get(role, role)}.', 'success')
    
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/<int:user_id>/files')
def user_files(user_id):
    """View all files for a specific user"""
    user = User.query.get_or_404(user_id)
    files = File.query.filter_by(user_id=user.id).order_by(File.created_at.desc()).all()
    
    return render_template('admin/user_files.html', user=user, files=files)


@admin_bp.route('/files/<int:file_id>/delete', methods=['POST'])
def delete_file(file_id):
    """Delete a file (admin only)"""
    file = File.query.get_or_404(file_id)
    
    file_number = file.file_number
    db.session.delete(file)
    db.session.commit()
    
    flash(f'Dossier {file_number} supprimé.', 'success')
    return redirect(url_for('admin.files'))


@admin_bp.route('/alerts')
def alerts():
    """View all files with alerts"""
    today = date.today()
    
    alert_files = File.query.filter(
        File.recall_date <= today,
        File.status != 'Finalized'
    ).order_by(File.recall_date).all()
    
    return render_template('admin/alerts.html', alert_files=alert_files, today=today)


@admin_bp.route('/trigger-recalls')
def trigger_recalls():
    """Manually trigger recall check and notifications"""
    from app import create_app
    from utils.scheduler import trigger_recall_check_now
    from flask import current_app
    
    try:
        trigger_recall_check_now(current_app._get_current_object())
        flash('Vérification des rappels effectuée avec succès! Les notifications ont été envoyées.', 'success')
    except Exception as e:
        flash(f'Erreur lors de la vérification des rappels: {str(e)}', 'danger')
    
    return redirect(url_for('admin.alerts'))


@admin_bp.route('/export/files')
def export_files():
    """Export all files to CSV"""
    from flask import make_response
    from utils.export import export_files_to_csv
    
    files = File.query.order_by(File.created_at.desc()).all()
    csv_data = export_files_to_csv(files)
    
    response = make_response(csv_data)
    response.headers['Content-Disposition'] = f'attachment; filename=fichiers_voc_{date.today().strftime("%Y%m%d")}.csv'
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    
    return response


@admin_bp.route('/export/users')
def export_users():
    """Export all users to CSV"""
    from flask import make_response
    from utils.export import export_users_to_csv
    
    users = User.query.order_by(User.created_at.desc()).all()
    csv_data = export_users_to_csv(users)
    
    response = make_response(csv_data)
    response.headers['Content-Disposition'] = f'attachment; filename=utilisateurs_voc_{date.today().strftime("%Y%m%d")}.csv'
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    
    return response