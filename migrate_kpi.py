"""
Migration pour ajouter la table status_history
"""
from app import create_app
from models import db
from sqlalchemy import text

def migrate_kpi():
    """Add status_history table"""
    app = create_app()
    
    with app.app_context():
        try:
            print("="*60)
            print("📊 MIGRATION KPI - Ajout de l'historique des statuts")
            print("="*60)
            print()
            
            # Create status_history table
            print("🔨 Création de la table status_history...")
            db.create_all()
            print("   ✅ Table créée")
            
            # Populate initial status history for existing files
            print("\n📝 Création de l'historique initial pour les dossiers existants...")
            from models import File, StatusHistory
            
            files = File.query.all()
            for file in files:
                # Create initial history entry
                history = StatusHistory(
                    file_id=file.id,
                    old_status=None,
                    new_status=file.status,
                    changed_at=file.created_at,
                    changed_by=file.user_id
                )
                db.session.add(history)
            
            db.session.commit()
            print(f"   ✅ Historique créé pour {len(files)} dossiers")
            
            print("\n" + "="*60)
            print("🎉 MIGRATION TERMINÉE!")
            print("="*60)
            print("\n📝 Les KPIs temporels sont maintenant disponibles!\n")
            
        except Exception as e:
            print(f"\n❌ Erreur: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    migrate_kpi()