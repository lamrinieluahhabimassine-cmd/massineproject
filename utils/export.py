"""
Data export utilities for CSV and Excel
"""
import csv
from io import StringIO, BytesIO
from datetime import datetime

def export_files_to_csv(files):
    """
    Export files to CSV format
    
    Args:
        files: List of File objects
        
    Returns:
        CSV string
    """
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'Numéro Dossier',
        'Date Réception',
        'Importateur',
        'Exportateur',
        'Pays',
        'Route',
        'Numéro SOR',
        'Numéro SOL',
        'Statut',
        'Date Rappel',
        'Utilisateur',
        'Email Utilisateur',
        'Date Création',
        'Dernière Modification',
        'CoC Numéro',
        'CoC Date',
        'Facture Numéro'
    ])
    
    # Write data
    for file in files:
        writer.writerow([
            file.file_number,
            file.receipt_date.strftime('%d/%m/%Y'),
            file.importer,
            file.exporter,
            file.country,
            file.route,
            file.sor_number or '',
            file.sol_number or '',
            file.status,
            file.recall_date.strftime('%d/%m/%Y') if file.recall_date else '',
            file.owner.username,
            file.owner.email,
            file.created_at.strftime('%d/%m/%Y %H:%M'),
            file.updated_at.strftime('%d/%m/%Y %H:%M'),
            file.coc_details.coc_number if file.coc_details else '',
            file.coc_details.coc_date.strftime('%d/%m/%Y') if file.coc_details else '',
            file.coc_details.invoice_number if file.coc_details else ''
        ])
    
    return output.getvalue()


def export_users_to_csv(users):
    """
    Export users to CSV format
    
    Args:
        users: List of User objects
        
    Returns:
        CSV string
    """
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'ID',
        'Nom d\'utilisateur',
        'Email',
        'Rôle',
        'Statut',
        'Date Création',
        'Nombre Dossiers',
        'Dossiers Finalisés'
    ])
    
    # Write data
    for user in users:
        from models import File
        total_files = File.query.filter_by(user_id=user.id).count()
        finalized_files = File.query.filter_by(user_id=user.id, status='Finalized').count()
        
        writer.writerow([
            user.id,
            user.username,
            user.email,
            user.role,
            'Actif' if user.is_active else 'Inactif',
            user.created_at.strftime('%d/%m/%Y %H:%M'),
            total_files,
            finalized_files
        ])
    
    return output.getvalue()


def export_statistics_to_csv(stats):
    """
    Export statistics summary to CSV
    
    Args:
        stats: Dictionary of statistics
        
    Returns:
        CSV string
    """
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Statistique', 'Valeur'])
    
    # Write data
    for key, value in stats.items():
        writer.writerow([key.replace('_', ' ').title(), value])
    
    return output.getvalue()