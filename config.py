import os
from dotenv import load_dotenv

# Load variables from .env file if it exists
load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'premium-college-dropout-prediction-secret-key-9988')
    
    # Database configuration credentials
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')  # Leave blank for default MySQL setups or SQLite fallback
    DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
    DB_PORT = os.getenv('DB_PORT', '3306')
    DB_NAME = os.getenv('DB_NAME', 'student_dropout_db')
    
    # Decide database engine
    # We will attempt to connect to MySQL if DB_PASSWORD is provided or if USE_MYSQL is set to true.
    # Otherwise, we fallback to SQLite locally in the project folder for seamless out-of-the-box operation.
    USE_MYSQL = os.getenv('USE_MYSQL', 'false').lower() == 'true' or (DB_PASSWORD != '')
    
    if USE_MYSQL:
        # Format: mysql+pymysql://username:password@host:port/database
        SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    else:
        # SQLite fallback in workspace
        basedir = os.path.abspath(os.path.dirname(__file__))
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(basedir, 'student_dropout.db')}"
        
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # SMTP configuration for alerts/notifications (Placeholder defaults)
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'dropout-alerts@college.edu')
