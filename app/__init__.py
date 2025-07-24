from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config

db = SQLAlchemy()
login_manager = LoginManager() # Buat instance LoginManager
login_manager.login_view = 'auth.login_staf' 
login_manager.login_message = 'Anda harus login untuk mengakses halaman ini.'
login_manager.login_message_category = 'info'

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    db.init_app(app)
    login_manager.init_app(app) # Inisialisasi login manager
    
    # Impor blueprint
    from .routes import main_bp
    from .auth import auth_bp
    from .admin import admin_bp
    from .petugas import petugas_bp
    from .pelanggan import pelanggan_bp
    
    # Daftarkan blueprint
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(petugas_bp, url_prefix='/petugas')
    app.register_blueprint(pelanggan_bp, url_prefix='/pelanggan')
    
    with app.app_context():
        from . import models

    return app



# Fungsi ini dibutuhkan oleh Flask-Login untuk mengambil data user dari sesi
from .models import Users
@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))