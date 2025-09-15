# ==============================================================================
# app.py - Main Application File
# Description: Initializes the Flask application, configures extensions,
#              registers blueprints, and sets up error handlers.
# ==============================================================================

# --- Core Flask Imports ---
# We're importing the main Flask class to create our application instance,
# and render_template to serve HTML files to the user.
import os
from flask import Flask, render_template

# --- Extensions ---
# These are add-ons for Flask that provide extra functionality.
from flask_wtf.csrf import CSRFProtect                  # Provides Cross-Site Request Forgery (CSRF) protection for our forms.

# --- Local Imports ---
# Here, we're bringing in our own code from other files in the project.
from config import config_by_name                       # Imports the application configuration classes from config.py.
from models import db, login_manager, Users, RateLimit  # Imports the database instance, login manager, and our User model.
from routes import auth_bp, admin_bp, quiz_bp           # Imports route blueprints for modular routing. This keeps our app organized.
from utils.email import email_service                   # Import email service for OTP functionality

# ==============================================================================
# Application Setup & Configuration
# ==============================================================================

def create_app(config_name='default'):
    """Application factory pattern for creating Flask app with specific configuration"""
    # Initialize the core Flask application.
    app = Flask(__name__)
    
    # Load configuration based on environment
    config_name = os.environ.get('FLASK_ENV', config_name)
    app.config.from_object(config_by_name.get(config_name, config_by_name['default']))
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    email_service.init_app(app)
    
    # Configure Flask-Login
    login_manager.login_view = 'auth.login'
    
    # Initialize CSRF protection
    csrf = CSRFProtect(app)
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(quiz_bp)
    
    # Template context processor
    @app.context_processor
    def inject_recaptcha_config():
        """Injects reCAPTCHA configuration into all Jinja2 templates."""
        return {
            'RECAPTCHA_PUBLIC_KEY': app.config.get('RECAPTCHA_PUBLIC_KEY'),
            'RECAPTCHA_ENABLED': app.config.get('RECAPTCHA_ENABLED', False),
            'RECAPTCHA_OPTIONS': app.config.get('RECAPTCHA_OPTIONS', {})
        }
    
    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        """Flask-Login calls this function to get the current user object."""
        return db.session.get(Users, int(user_id))
    
    # Database initialization
    with app.app_context():
        db.create_all()
    
    return app

# ==============================================================================
# Development Server and Application Instance
# ==============================================================================

# Create the application instance
app = create_app()

# ==============================================================================
# Development Server Entry Point
# ==============================================================================

# This is a standard Python construct. The code inside this block will only run
# when this script is executed directly (e.g., by running `python app.py`).
# It won't run if this file is imported by another script.
if __name__ == "__main__":
    # Get configuration from environment variables for production readiness
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    port = int(os.environ.get('PORT', 5002))
    host = os.environ.get('HOST', '127.0.0.1')
    
    # This starts the built-in Flask development server.
    # Debug mode is controlled by environment variable for production safety
    # In production, Gunicorn will handle serving the app instead
    app.run(debug=debug_mode, port=port, host=host)