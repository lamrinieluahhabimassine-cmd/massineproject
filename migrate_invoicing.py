"""
Migration script to add invoicing fields to existing database
Run this once: python migrate_invoicing.py
"""
from app import create_app
from models import db
from sqlalchemy import text

def migrate_database():
    """Add invoicing fields to File model"""
    app = create_app()
    
    with app.app_context():
        try:
            print("="*60)
            print("🔍 CHECKING DATABASE STRUCTURE")
            print("="*60)
            
            # Check if columns already exist
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('files')]
            
            print(f"\n📊 Found {len(columns)} existing columns in 'files' table")
            print("\n⚙️  Starting migration...\n")
            
            # Add new columns if they don't exist
            with db.engine.connect() as conn:
                if 'mar_number' not in columns:
                    print("➕ Adding mar_number column...")
                    conn.execute(text('ALTER TABLE files ADD COLUMN mar_number VARCHAR(100)'))
                    conn.commit()
                    print("   ✅ Added mar_number column")
                else:
                    print("   ⏭️  mar_number already exists")
                
                if 'proforma_number' not in columns:
                    print("➕ Adding proforma_number column...")
                    conn.execute(text('ALTER TABLE files ADD COLUMN proforma_number VARCHAR(100)'))
                    conn.commit()
                    print("   ✅ Added proforma_number column")
                else:
                    print("   ⏭️  proforma_number already exists")
                
                if 'payment_justification_path' not in columns:
                    print("➕ Adding payment_justification_path column...")
                    conn.execute(text('ALTER TABLE files ADD COLUMN payment_justification_path VARCHAR(500)'))
                    conn.commit()
                    print("   ✅ Added payment_justification_path column")
                else:
                    print("   ⏭️  payment_justification_path already exists")
                
                if 'invoiced_at' not in columns:
                    print("➕ Adding invoiced_at column...")
                    conn.execute(text('ALTER TABLE files ADD COLUMN invoiced_at DATETIME'))
                    conn.commit()
                    print("   ✅ Added invoiced_at column")
                else:
                    print("   ⏭️  invoiced_at already exists")
                
                if 'invoiced_by' not in columns:
                    print("➕ Adding invoiced_by column...")
                    conn.execute(text('ALTER TABLE files ADD COLUMN invoiced_by INTEGER'))
                    conn.commit()
                    print("   ✅ Added invoiced_by column")
                else:
                    print("   ⏭️  invoiced_by already exists")
            
            print("\n" + "="*60)
            print("🎉 MIGRATION COMPLETED SUCCESSFULLY!")
            print("="*60)
            print("\n📝 Next steps:")
            print("   1. Run: python app.py")
            print("   2. Login and test!")
            print("   3. Create invoicing users\n")
            
        except Exception as e:
            print("\n" + "="*60)
            print("❌ MIGRATION FAILED")
            print("="*60)
            print(f"\nError: {e}\n")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 STARTING DATABASE MIGRATION FOR INVOICING")
    print("="*60)
    print()
    migrate_database()