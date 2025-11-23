"""
Scheduled tasks for automated recall notifications
"""
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import date
import logging

logger = logging.getLogger(__name__)

def check_and_send_recalls(app):
    """
    Check for files with recall_date <= today and send notifications
    This function runs daily
    """
    with app.app_context():
        from models import File, User, Notification, db
        from utils.email import send_recall_notification
        
        today = date.today()
        
        # Find files that need recall and are not finalized
        files_to_recall = File.query.filter(
            File.recall_date <= today,
            File.status != 'Finalized'
        ).all()
        
        if not files_to_recall:
            logger.info("No files to recall today.")
            return
        
        logger.info(f"Found {len(files_to_recall)} files to recall")
        
        # Get all admin emails for CC
        admin_users = User.query.filter_by(role='admin').all()
        admin_emails = [admin.email for admin in admin_users]
        
        # Process each file
        for file in files_to_recall:
            try:
                # Get file owner
                user = file.owner
                
                # Check if notification already sent today
                existing_notif = Notification.query.filter(
                    Notification.file_id == file.id,
                    Notification.notification_type == 'recall',
                    Notification.created_at >= today
                ).first()
                
                if existing_notif:
                    logger.info(f"Notification already sent today for file {file.file_number}")
                    continue
                
                # Send email notification
                email_sent = send_recall_notification(
                    file=file,
                    user=user,
                    admin_emails=admin_emails
                )
                
                # Create in-app notification
                notification = Notification(
                    message=f"Rappel: Le dossier {file.file_number} nécessite votre attention (Date de rappel: {file.recall_date.strftime('%d/%m/%Y')})",
                    user_id=user.id,
                    file_id=file.id,
                    notification_type='recall',
                    read_status=False
                )
                db.session.add(notification)
                
                # Also create notification for admins
                for admin in admin_users:
                    admin_notif = Notification(
                        message=f"Rappel pour {user.username}: Dossier {file.file_number} (Date: {file.recall_date.strftime('%d/%m/%Y')})",
                        user_id=admin.id,
                        file_id=file.id,
                        notification_type='recall',
                        read_status=False
                    )
                    db.session.add(admin_notif)
                
                db.session.commit()
                
                logger.info(f"Recall notification sent for file {file.file_number} to {user.email}")
                
            except Exception as e:
                logger.error(f"Error processing recall for file {file.file_number}: {str(e)}")
                db.session.rollback()
                continue
        
        logger.info("Recall check completed")


def init_scheduler(app):
    """
    Initialize and start the background scheduler
    
    Args:
        app: Flask application instance
    """
    scheduler = BackgroundScheduler()
    
    # Schedule the recall check to run daily at 9:00 AM
    scheduler.add_job(
        func=lambda: check_and_send_recalls(app),
        trigger='cron',
        hour=9,
        minute=0,
        id='daily_recall_check',
        name='Check and send recall notifications',
        replace_existing=True
    )
    
    # For testing: also run immediately on startup
    scheduler.add_job(
        func=lambda: check_and_send_recalls(app),
        trigger='date',
        id='startup_recall_check',
        name='Initial recall check on startup'
    )
    
    scheduler.start()
    logger.info("Scheduler started - Daily recall checks enabled at 9:00 AM")
    
    return scheduler


def trigger_recall_check_now(app):
    """
    Manually trigger a recall check (for testing or manual execution)
    
    Args:
        app: Flask application instance
    """
    logger.info("Manual recall check triggered")
    check_and_send_recalls(app)