import os
from dotenv import load_dotenv

# Load environment variables from a .env file into the application's environment.
# This makes it easy to manage configuration settings for development.
load_dotenv()

class Config:
    """
    Sets the configuration for the Flask app.
    Values are loaded from environment variables to keep sensitive data
    and settings out of the source code.
    """
    # --- Database ---
    # The connection string for the application's database.
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    
    # Disables a deprecated Flask-SQLAlchemy event system to improve performance.
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # --- Security ---
    # A secret key used to cryptographically sign session cookies and other data.
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    # --- Templates ---
    # For development: automatically reloads templates when they are modified.
    TEMPLATES_AUTO_RELOAD = True
    
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