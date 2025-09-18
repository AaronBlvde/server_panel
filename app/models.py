from . import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    roles = db.relationship("Role", backref="user", uselist=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    view = db.Column(db.Boolean, default=True)        # может смотреть контейнеры и логи
    start_stop = db.Column(db.Boolean, default=False) # может запускать/останавливать контейнеры
    rebuild = db.Column(db.Boolean, default=False)    # может пересобирать контейнеры


# Новая модель для хранения пути к Dockerfile для каждого контейнера
class ContainerConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    container_name = db.Column(db.String(100), unique=True, nullable=False)
    last_build_path = db.Column(db.String(500), nullable=True)
