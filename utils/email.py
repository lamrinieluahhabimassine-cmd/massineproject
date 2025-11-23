"""
Email utility functions for sending notifications
"""
from flask import render_template_string
from flask_mail import Message
from app import mail
import logging

logger = logging.getLogger(__name__)

def send_email(subject, recipients, html_body, text_body=None, cc=None):
    """
    Send email with HTML body
    
    Args:
        subject: Email subject
        recipients: List of recipient email addresses
        html_body: HTML content
        text_body: Plain text content (optional)
        cc: List of CC email addresses (optional)
    """
    try:
        msg = Message(
            subject=subject,
            recipients=recipients,
            html=html_body,
            body=text_body or "Veuillez consulter la version HTML de cet email."
        )
        
        if cc:
            msg.cc = cc
        
        mail.send(msg)
        logger.info(f"Email sent to {recipients}: {subject}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {recipients}: {str(e)}")
        return False


def send_recall_notification(file, user, admin_emails=None):
    """
    Send recall notification for a file
    
    Args:
        file: File object
        user: User object (file owner)
        admin_emails: List of admin emails to CC (optional)
    """
    subject = f"Rappel: Dossier {file.file_number} nécessite votre attention"
    
    # HTML email template
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f9f9f9;
            }}
            .header {{
                background-color: #FFB81C;
                color: #1A1A1A;
                padding: 20px;
                text-align: center;
            }}
            .content {{
                background-color: white;
                padding: 30px;
                margin-top: 20px;
                border-radius: 5px;
            }}
            .alert {{
                background-color: #fff3cd;
                border-left: 4px solid #ffc107;
                padding: 15px;
                margin: 20px 0;
            }}
            .file-details {{
                background-color: #f8f9fa;
                padding: 15px;
                border-radius: 5px;
                margin: 20px 0;
            }}
            .file-details p {{
                margin: 5px 0;
            }}
            .footer {{
                text-align: center;
                margin-top: 20px;
                color: #666;
                font-size: 12px;
            }}
            .btn {{
                display: inline-block;
                padding: 12px 24px;
                background-color: #003DA5;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                margin: 20px 0;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔔 VOC Platform - Rappel de Dossier</h1>
            </div>
            
            <div class="content">
                <p>Bonjour <strong>{user.username}</strong>,</p>
                
                <div class="alert">
                    <strong>⚠️ Attention:</strong> Le dossier suivant a atteint sa date de rappel et nécessite votre attention.
                </div>
                
                <div class="file-details">
                    <h3>Détails du Dossier:</h3>
                    <p><strong>Numéro:</strong> {file.file_number}</p>
                    <p><strong>Importateur:</strong> {file.importer}</p>
                    <p><strong>Exportateur:</strong> {file.exporter}</p>
                    <p><strong>Pays:</strong> {file.country}</p>
                    <p><strong>Route:</strong> {file.route}</p>
                    <p><strong>Statut actuel:</strong> {file.status}</p>
                    <p><strong>Date de rappel:</strong> {file.recall_date.strftime('%d/%m/%Y')}</p>
                </div>
                
                <p>Veuillez vous connecter à la plateforme pour mettre à jour ce dossier:</p>
                
                <center>
                    <a href="http://127.0.0.1:5000/user/files/{file.id}" class="btn">
                        Voir le Dossier
                    </a>
                </center>
                
                <p style="margin-top: 30px;">Cordialement,<br><strong>VOC Platform - Intertek Morocco</strong></p>
            </div>
            
            <div class="footer">
                <p>Ceci est un message automatique, merci de ne pas y répondre.</p>
                <p>&copy; 2025 Intertek Morocco - VOC Visibility Enhancer</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Plain text version
    text_body = f"""
    Rappel: Dossier {file.file_number}
    
    Bonjour {user.username},
    
    Le dossier {file.file_number} a atteint sa date de rappel ({file.recall_date.strftime('%d/%m/%Y')}) 
    et nécessite votre attention.
    
    Détails:
    - Importateur: {file.importer}
    - Exportateur: {file.exporter}
    - Pays: {file.country}
    - Route: {file.route}
    - Statut: {file.status}
    
    Veuillez vous connecter à la plateforme pour mettre à jour ce dossier.
    
    Cordialement,
    VOC Platform - Intertek Morocco
    """
    
    return send_email(
        subject=subject,
        recipients=[user.email],
        html_body=html_body,
        text_body=text_body,
        cc=admin_emails
    )


def send_status_change_notification(file, user, old_status, new_status):
    """
    Send notification when file status changes
    
    Args:
        file: File object
        user: User object
        old_status: Previous status
        new_status: New status
    """
    subject = f"Changement de statut: Dossier {file.file_number}"
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f9f9f9;
            }}
            .header {{
                background-color: #003DA5;
                color: white;
                padding: 20px;
                text-align: center;
            }}
            .content {{
                background-color: white;
                padding: 30px;
                margin-top: 20px;
                border-radius: 5px;
            }}
            .status-change {{
                background-color: #e7f3ff;
                border-left: 4px solid #007bff;
                padding: 15px;
                margin: 20px 0;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📝 Changement de Statut</h1>
            </div>
            
            <div class="content">
                <p>Bonjour <strong>{user.username}</strong>,</p>
                
                <p>Le statut du dossier <strong>{file.file_number}</strong> a été modifié.</p>
                
                <div class="status-change">
                    <p><strong>Ancien statut:</strong> {old_status}</p>
                    <p><strong>Nouveau statut:</strong> {new_status}</p>
                </div>
                
                <p>Détails du dossier:</p>
                <ul>
                    <li><strong>Importateur:</strong> {file.importer}</li>
                    <li><strong>Exportateur:</strong> {file.exporter}</li>
                    <li><strong>Pays:</strong> {file.country}</li>
                </ul>
                
                <p style="margin-top: 30px;">Cordialement,<br><strong>VOC Platform</strong></p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_email(
        subject=subject,
        recipients=[user.email],
        html_body=html_body
    )


def send_coc_added_notification(file, user, coc_details):
    """
    Send notification when CoC details are added
    
    Args:
        file: File object
        user: User object
        coc_details: CoCDetails object
    """
    subject = f"CoC ajouté: Dossier {file.file_number}"
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f9f9f9;
            }}
            .header {{
                background-color: #28a745;
                color: white;
                padding: 20px;
                text-align: center;
            }}
            .content {{
                background-color: white;
                padding: 30px;
                margin-top: 20px;
                border-radius: 5px;
            }}
            .coc-details {{
                background-color: #d4edda;
                border-left: 4px solid #28a745;
                padding: 15px;
                margin: 20px 0;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🏆 Certificate of Conformity Ajouté</h1>
            </div>
            
            <div class="content">
                <p>Bonjour <strong>{user.username}</strong>,</p>
                
                <p>Les détails du Certificate of Conformity ont été ajoutés au dossier <strong>{file.file_number}</strong>.</p>
                
                <div class="coc-details">
                    <h3>Détails CoC:</h3>
                    <p><strong>Numéro CoC:</strong> {coc_details.coc_number}</p>
                    <p><strong>Date CoC:</strong> {coc_details.coc_date.strftime('%d/%m/%Y')}</p>
                    <p><strong>Numéro de Facture:</strong> {coc_details.invoice_number}</p>
                </div>
                
                <p>Le dossier est maintenant complètement finalisé.</p>
                
                <p style="margin-top: 30px;">Cordialement,<br><strong>VOC Platform</strong></p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_email(
        subject=subject,
        recipients=[user.email],
        html_body=html_body
    )