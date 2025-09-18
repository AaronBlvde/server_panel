from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "main.login"


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)

    from .routes import main
    app.register_blueprint(main)

    with app.app_context():
        from .models import User, Role
        db.create_all()
        # Создание админа по умолчанию
        if not User.query.filter_by(username="admin").first():
            admin = User(username="admin", is_admin=True)
            admin.set_password("admin123")  # сменить на безопасный пароль
            db.session.add(admin)
            db.session.commit()
            # Даем администратору все права
            roles = Role(user_id=admin.id, view=True, start_stop=True, rebuild=True)
            db.session.add(roles)
            db.session.commit()

    return app
