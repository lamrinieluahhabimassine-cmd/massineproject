"""
Automatic backup system for database and files
"""
import os
import shutil
import gzip
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class BackupManager:
    """Manage database and file backups"""
    
    def __init__(self, app):
        self.app = app
        self.backup_dir = os.path.join(app.root_path, 'backups')
        self.ensure_backup_directory()
    
    def ensure_backup_directory(self):
        """Create backup directory if it doesn't exist"""
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
            logger.info(f"Created backup directory: {self.backup_dir}")
    
    def backup_database(self):
        """
        Backup SQLite database
        For PostgreSQL, use pg_dump command
        """
        try:
            db_path = self.app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
            
            if not os.path.exists(db_path):
                logger.warning(f"Database file not found: {db_path}")
                return False
            
            # Generate backup filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"database_backup_{timestamp}.db"
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            # Copy database file
            shutil.copy2(db_path, backup_path)
            
            # Compress backup
            compressed_path = f"{backup_path}.gz"
            with open(backup_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Remove uncompressed backup
            os.remove(backup_path)
            
            logger.info(f"Database backup created: {compressed_path}")
            
            # Clean old backups (keep last 7 days)
            self.cleanup_old_backups(days=7)
            
            return compressed_path
            
        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            return False
    
    def backup_uploads(self):
        """Backup uploaded files directory"""
        try:
            uploads_dir = os.path.join(self.app.root_path, 'uploads')
            
            if not os.path.exists(uploads_dir):
                logger.warning("Uploads directory not found")
                return False
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"uploads_backup_{timestamp}"
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            # Create tar.gz archive
            shutil.make_archive(backup_path, 'gztar', uploads_dir)
            
            logger.info(f"Uploads backup created: {backup_path}.tar.gz")
            
            return f"{backup_path}.tar.gz"
            
        except Exception as e:
            logger.error(f"Uploads backup failed: {e}")
            return False
    
    def full_backup(self):
        """Perform full backup (database + files)"""
        logger.info("Starting full backup...")
        
        db_backup = self.backup_database()
        files_backup = self.backup_uploads()
        
        if db_backup and files_backup:
            logger.info("Full backup completed successfully")
            return True
        else:
            logger.warning("Full backup completed with errors")
            return False
    
    def cleanup_old_backups(self, days=7):
        """Remove backups older than specified days"""
        try:
            cutoff_time = datetime.now().timestamp() - (days * 86400)
            
            for filename in os.listdir(self.backup_dir):
                file_path = os.path.join(self.backup_dir, filename)
                
                if os.path.isfile(file_path):
                    file_time = os.path.getmtime(file_path)
                    
                    if file_time < cutoff_time:
                        os.remove(file_path)
                        logger.info(f"Removed old backup: {filename}")
            
            logger.info(f"Cleanup completed - removed backups older than {days} days")
            
        except Exception as e:
            logger.error(f"Backup cleanup failed: {e}")
    
    def restore_database(self, backup_file):
        """Restore database from backup"""
        try:
            backup_path = os.path.join(self.backup_dir, backup_file)
            
            if not os.path.exists(backup_path):
                logger.error(f"Backup file not found: {backup_path}")
                return False
            
            # Decompress if needed
            if backup_path.endswith('.gz'):
                decompressed_path = backup_path[:-3]
                with gzip.open(backup_path, 'rb') as f_in:
                    with open(decompressed_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                restore_from = decompressed_path
            else:
                restore_from = backup_path
            
            # Get database path
            db_path = self.app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
            
            # Backup current database before restore
            if os.path.exists(db_path):
                backup_current = f"{db_path}.before_restore"
                shutil.copy2(db_path, backup_current)
                logger.info(f"Current database backed up to: {backup_current}")
            
            # Restore
            shutil.copy2(restore_from, db_path)
            
            # Clean up decompressed file
            if backup_path.endswith('.gz') and os.path.exists(decompressed_path):
                os.remove(decompressed_path)
            
            logger.info(f"Database restored from: {backup_file}")
            return True
            
        except Exception as e:
            logger.error(f"Database restore failed: {e}")
            return False
    
    def list_backups(self):
        """List all available backups"""
        backups = []
        
        try:
            for filename in os.listdir(self.backup_dir):
                file_path = os.path.join(self.backup_dir, filename)
                
                if os.path.isfile(file_path):
                    stat = os.stat(file_path)
                    backups.append({
                        'filename': filename,
                        'size': stat.st_size,
                        'created': datetime.fromtimestamp(stat.st_mtime),
                        'type': 'database' if 'database' in filename else 'uploads'
                    })
            
            # Sort by creation date, newest first
            backups.sort(key=lambda x: x['created'], reverse=True)
            
        except Exception as e:
            logger.error(f"Failed to list backups: {e}")
        
        return backups
    
    def get_backup_size(self):
        """Get total size of all backups"""
        total_size = 0
        
        try:
            for filename in os.listdir(self.backup_dir):
                file_path = os.path.join(self.backup_dir, filename)
                if os.path.isfile(file_path):
                    total_size += os.path.getsize(file_path)
        except Exception as e:
            logger.error(f"Failed to calculate backup size: {e}")
        
        return total_size


def schedule_backups(app, scheduler):
    """
    Schedule automatic backups
    Add to scheduler initialization
    """
    backup_manager = BackupManager(app)
    
    # Daily backup at 2:00 AM
    scheduler.add_job(
        func=lambda: backup_manager.full_backup(),
        trigger='cron',
        hour=2,
        minute=0,
        id='daily_backup',
        name='Daily full backup',
        replace_existing=True
    )
    
    logger.info("Automatic backups scheduled - Daily at 2:00 AM")
    
    return backup_manager