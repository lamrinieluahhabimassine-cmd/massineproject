"""
Database initialization script
Creates tables and adds initial admin user
"""
from app import create_app
from models import db, User
from getpass import getpass

def init_database():
    """Initialize database and create admin user"""
    app = create_app()
    
    with app.app_context():
        # Create all tables
        print("Creating database tables...")
        db.create_all()
        print("✅ Tables created successfully!")
        
        # Check if admin already exists
        admin = User.query.filter_by(role='admin').first()
        
        if admin:
            print(f"\n⚠️  Admin user already exists: {admin.username} ({admin.email})")
            response = input("Do you want to create another admin? (y/n): ")
            if response.lower() != 'y':
                print("Exiting...")
                return
        
        # Get admin details
        print("\n" + "="*50)
        print("CREATE ADMIN USER")
        print("="*50)
        
        username = input("Enter admin username: ").strip()
        email = input("Enter admin email: ").strip()
        password = getpass("Enter admin password: ")
        password_confirm = getpass("Confirm password: ")
        
        # Validate inputs
        if not username or not email or not password:
            print("❌ All fields are required!")
            return
        
        if password != password_confirm:
            print("❌ Passwords don't match!")
            return
        
        # Check if username or email already exists
        if User.query.filter_by(username=username).first():
            print(f"❌ Username '{username}' already exists!")
            return
        
        if User.query.filter_by(email=email).first():
            print(f"❌ Email '{email}' already exists!")
            return
        
        # Create admin user
        admin = User(
            username=username,
            email=email,
            role='admin',
            is_active=True
        )
        admin.set_password(password)
        
        db.session.add(admin)
        db.session.commit()
        
        print("\n" + "="*50)
        print("✅ ADMIN USER CREATED SUCCESSFULLY!")
        print("="*50)
        print(f"Username: {username}")
        print(f"Email: {email}")
        print(f"Role: admin")
        print("\nYou can now log in with these credentials.")
        print("="*50)

def create_test_user():
    """Create a test regular user for development"""
    app = create_app()
    
    with app.app_context():
        # Check if test user exists
        test_user = User.query.filter_by(username='testuser').first()
        
        if test_user:
            print("⚠️  Test user already exists")
            return
        
        print("\nCreating test user...")
        user = User(
            username='testuser',
            email='testuser@intertek.com',
            role='user',
            is_active=True
        )
        user.set_password('test123')
        
        db.session.add(user)
        db.session.commit()
        
        print("✅ Test user created!")
        print("Username: testuser")
        print("Password: test123")

def show_all_users():
    """Display all users in the database"""
    app = create_app()
    
    with app.app_context():
        users = User.query.all()
        
        if not users:
            print("No users found in database.")
            return
        
        print("\n" + "="*70)
        print("ALL USERS IN DATABASE")
        print("="*70)
        print(f"{'ID':<5} {'Username':<20} {'Email':<30} {'Role':<10}")
        print("-"*70)
        
        for user in users:
            print(f"{user.id:<5} {user.username:<20} {user.email:<30} {user.role:<10}")
        
        print("="*70)
        print(f"Total users: {len(users)}")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'admin':
            init_database()
        elif command == 'testuser':
            create_test_user()
        elif command == 'list':
            show_all_users()
        else:
            print("Unknown command!")
            print("Usage:")
            print("  python init_db.py admin     - Create admin user")
            print("  python init_db.py testuser  - Create test user")
            print("  python init_db.py list      - List all users")
    else:
        # Default: create admin
        init_database()