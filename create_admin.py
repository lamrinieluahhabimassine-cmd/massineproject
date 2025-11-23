"""
Script pour créer un admin en production
Usage: python create_admin.py <username> <email> <password>
"""
import sys
from app import create_app
from models import db, User

def create_admin(username, email, password):
    """Créer un utilisateur admin"""
    app = create_app()
    
    with app.app_context():
        # Créer les tables si elles n'existent pas
        db.create_all()
        
        # Vérifier si l'utilisateur existe déjà
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            print(f"❌ Utilisateur {username} existe déjà!")
            return False
        
        # Créer l'admin
        admin = User(
            username=username,
            email=email,
            role='admin',
            is_active=True
        )
        admin.set_password(password)
        
        db.session.add(admin)
        db.session.commit()
        
        print(f"✅ Admin {username} créé avec succès!")
        return True

if __name__ == '__main__':
    if len(sys.argv) != 4:
        print("Usage: python create_admin.py <username> <email> <password>")
        print("Exemple: python create_admin.py admin admin@intertek.com MySecurePass123")
        sys.exit(1)
    
    username = sys.argv[1]
    email = sys.argv[2]
    password = sys.argv[3]
    
    create_admin(username, email, password)