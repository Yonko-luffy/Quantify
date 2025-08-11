import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Security Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    # Template Configuration
    TEMPLATES_AUTO_RELOAD = True
    
    # reCAPTCHA Configuration
    RECAPTCHA_PUBLIC_KEY = os.environ.get('RECAPTCHA_PUBLIC_KEY')
    RECAPTCHA_PRIVATE_KEY = os.environ.get('RECAPTCHA_PRIVATE_KEY')
    RECAPTCHA_ENABLED = os.environ.get('RECAPTCHA_ENABLED', 'False').lower() == 'true'
    RECAPTCHA_USE_SSL = os.environ.get('RECAPTCHA_USE_SSL', 'False').lower() == 'true'
    RECAPTCHA_OPTIONS = {
        'theme': os.environ.get('RECAPTCHA_THEME', 'light'),
        'type': os.environ.get('RECAPTCHA_TYPE', 'image'),
        'size': os.environ.get('RECAPTCHA_SIZE', 'normal')
    }
