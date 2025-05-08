from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your_secret_key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth_bp.login'
    login_manager.login_message = "Silakan login untuk mengakses halaman ini."
    login_manager.login_message_category = "warning"

    # Register blueprints
    from .routes.auth import auth_bp
    from .routes.main import main_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)

    return app

@login_manager.user_loader
def load_user(user_id):
    from .models import User
    return User.query.get(int(user_id))