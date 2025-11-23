from flask import Flask
from flask_login import LoginManager
from flask_mail import Mail
import os

# Initialize extensions (without app)
login_manager = LoginManager()
mail = Mail()

def create_app():
    app = Flask(__name__)
    
    # Import db from models
    from models import db
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///voc_platform.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Mail configuration
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@intertek.com')
    
    # File upload configuration
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    app.config['UPLOAD_FOLDER'] = 'uploads'
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    
    # Login manager configuration
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'
    
    # Import user loader
    from models import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register blueprints
    from routes.evaluator import evaluator_bp
    from routes.auth import auth_bp
    from routes.user import user_bp
    from routes.admin import admin_bp
    from routes.errors import errors_bp
    from routes.invoice import invoice_bp
    from routes.affecteur import affecteur_bp
    from routes.kpi import kpi_bp  
    
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(errors_bp)
    app.register_blueprint(invoice_bp)
    app.register_blueprint(affecteur_bp)
    app.register_blueprint(kpi_bp) 
    app.register_blueprint(evaluator_bp)
    # Create database tables
    with app.app_context():
        db.create_all()
    
    # Initialize scheduler for automated recalls
    from utils.scheduler import init_scheduler
    init_scheduler(app)
    
    return app

if __name__ == '__main__':
    app = create_app()
    # Pour production, utilisez gunicorn
    # Pour dev local, utilisez debug=True
    import os
    debug_mode = os.environ.get('FLASK_ENV', 'development') == 'development'
    app.run(debug=debug_mode, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))