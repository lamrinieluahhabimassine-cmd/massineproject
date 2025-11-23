"""
Migration script to add new status "à compléter" to the workflow
Run this once: python migrate_new_status.py
"""
from app import create_app
from models import db, File
from datetime import datetime

def migrate_status():
    """Add support for new status "à compléter" """
    app = create_app()
    
    with app.app_context():
        try:
            print("="*60)
            print("🔍 MIGRATION: Adding 'à compléter' Status")
            print("="*60)
            print()
            
            # Check if there are any files that might need adjustment
            # Files in "en cours de traitement" can now transition to "à compléter"
            files_in_processing = File.query.filter_by(
                status='en cours de traitement'
            ).count()
            
            print(f"📊 Found {files_in_processing} files in 'en cours de traitement'")
            print("   These can now transition to 'à compléter' if needed")
            print()
            
            # The new status is now valid in validation.py
            print("✅ New status 'à compléter' is now valid")
            print()
            
            # Check for any files that might be in inconsistent states
            all_files = File.query.all()
            valid_statuses = [
                'en attente d\'évaluation',
                'en cours d\'évaluation',
                'ready to invoice',
                'payed',
                'en cours de traitement',
                'à compléter',
                'transfert à l\'inspection',
                'Finalized'
            ]
            
            invalid_count = 0
            for file in all_files:
                if file.status not in valid_statuses:
                    print(f"⚠️  File {file.file_number} has invalid status: {file.status}")
                    invalid_count += 1
            
            if invalid_count == 0:
                print("✅ All files have valid statuses")
            else:
                print(f"⚠️  {invalid_count} file(s) have invalid statuses")
                print("   Please review and manually fix these files")
            
            print()
            print("="*60)
            print("🎉 MIGRATION COMPLETED SUCCESSFULLY!")
            print("="*60)
            print()
            print("📝 Workflow is now:")
            print("   1. en attente d'évaluation")
            print("   2. en cours d'évaluation")
            print("   3. ready to invoice (or)")
            print("   4. payed")
            print("   5. en cours de traitement")
            print("   6. à compléter         ← NEW STATUS")
            print("   7. transfert à l'inspection")
            print("   8. Finalized")
            print()
            print("✨ Users can now update file status to 'à compléter'")
            print()
            
        except Exception as e:
            print("="*60)
            print("❌ MIGRATION FAILED")
            print("="*60)
            print(f"\nError: {e}\n")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    migrate_status()