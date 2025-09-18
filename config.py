import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "supersecretkey"
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or "postgresql://postgres:postgres@db:5432/panel"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
