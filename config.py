import os
from dotenv import load_dotenv

# Load environment variables from a .env file into the application's environment.
# This makes it easy to manage configuration settings for development.
load_dotenv()

class Config:
    """
    Base configuration for the Flask app.
    Values are loaded from environment variables to keep sensitive data
    and settings out of the source code.
    """
    # --- Database ---
    # The connection string for the application's database.
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("postgres://", "postgresql://", 1)
    
    # Disables a deprecated Flask-SQLAlchemy event system to improve performance.
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # --- Security ---
    # A secret key used to cryptographically sign session cookies and other data.
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    # --- Environment Detection ---
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    # --- Templates ---
    # For development: automatically reloads templates when they are modified.
    TEMPLATES_AUTO_RELOAD = os.environ.get('TEMPLATES_AUTO_RELOAD', 'True').lower() == 'true'
    
    # --- Google reCAPTCHA ---
    # API keys for the reCAPTCHA service.
    RECAPTCHA_PUBLIC_KEY = os.environ.get('RECAPTCHA_PUBLIC_KEY')    # Front-end site key
    RECAPTCHA_PRIVATE_KEY = os.environ.get('RECAPTCHA_PRIVATE_KEY')  # Back-end secret key
    
    # Master switch for the feature. Converts env string 'true' to a boolean.
    RECAPTCHA_ENABLED = os.environ.get('RECAPTCHA_ENABLED', 'False').lower() == 'true'
    RECAPTCHA_USE_SSL = os.environ.get('RECAPTCHA_USE_SSL', 'False').lower() == 'true'
    
    # Options to configure the front-end reCAPTCHA widget.
    RECAPTCHA_OPTIONS = {
        'theme': os.environ.get('RECAPTCHA_THEME', 'light'),
        'type': os.environ.get('RECAPTCHA_TYPE', 'image'),
        'size': os.environ.get('RECAPTCHA_SIZE', 'normal')
    }
    
    # --- Email Configuration ---
    # SMTP settings for sending OTP emails
    # TODO: Add these to your .env file:
    # MAIL_SERVER=smtp.gmail.com
    # MAIL_PORT=587
    # MAIL_USE_TLS=True
    # MAIL_USERNAME=your-email@gmail.com
    # MAIL_PASSWORD=your-app-password
    # MAIL_DEFAULT_SENDER=your-email@gmail.com
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'False').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    
    # --- 2FA & Password Reset Configuration ---
    # TODO: Add these to your .env file:
    # OTP_LENGTH=6
    # OTP_EXPIRY_MINUTES=5
    # TWO_FA_ENABLED=True
    # PASSWORD_RESET_ENABLED=True
    OTP_LENGTH = int(os.environ.get('OTP_LENGTH', 6))
    OTP_EXPIRY_MINUTES = int(os.environ.get('OTP_EXPIRY_MINUTES', 5))
    TWO_FA_ENABLED = os.environ.get('TWO_FA_ENABLED', 'True').lower() == 'true'
    PASSWORD_RESET_ENABLED = os.environ.get('PASSWORD_RESET_ENABLED', 'True').lower() == 'true'


class DevelopmentConfig(Config):
    """Configuration for development environment"""
    DEBUG = True
    TEMPLATES_AUTO_RELOAD = True
    SQLALCHEMY_ECHO = False  # Set to True to see SQL queries in logs


class ProductionConfig(Config):
    """Configuration for production environment"""
    DEBUG = False
    TEMPLATES_AUTO_RELOAD = False
    SQLALCHEMY_ECHO = False
    
    # Production security settings
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Force HTTPS in production
    PREFERRED_URL_SCHEME = 'https'


class TestingConfig(Config):
    """Configuration for testing environment"""
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


# Configuration dictionary
config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}