import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///dineiq_app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev")
    JWT_ACCESS_TOKEN_EXPIRES = 900
    JWT_REFRESH_TOKEN_EXPIRES = 604800
    BCRYPT_ROUNDS = int(os.getenv("BCRYPT_ROUNDS", 12))
    MAX_LOGIN_ATTEMPTS = int(os.getenv("MAX_LOGIN_ATTEMPTS", 5))
