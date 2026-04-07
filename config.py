from datetime import timedelta
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY                     = os.getenv("SECRET_KEY", "dme_secret_key_2026")
    SQLALCHEMY_DATABASE_URI        = os.getenv("DATABASE_URL", "sqlite:///dme.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY                 = os.getenv("JWT_SECRET_KEY", "jwt_dme_secret_2026")
    JWT_ACCESS_TOKEN_EXPIRES       = timedelta(hours=3)