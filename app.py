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
        
        # Auto-create sample quiz data if none exists
        from models import Category, Question, Quiz
        try:
            # Check specifically for sample quiz data (not all quiz data)
            sample_categories = [
                "Numerical Ability", "Logical Reasoning", "Data Interpretation", 
                "Analytical Reasoning", "Mathematical Operations"
            ]
            
            existing_sample_categories = Category.query.filter(
                Category.name.in_(sample_categories)
            ).count()
            
            sample_quiz_names = [
                "Numerical Aptitude Foundation", "Logical Reasoning Mastery", 
                "Complete Quantitative Aptitude"
            ]
            
            existing_sample_quizzes = Quiz.query.filter(
                Quiz.name.in_(sample_quiz_names)
            ).count()
            
            # Only create sample data if we don't have the core sample quizzes
            sample_data_exists = (existing_sample_categories >= 3 and existing_sample_quizzes >= 2)
            
            total_categories = Category.query.count()
            total_questions = Question.query.count()
            total_quizzes = Quiz.query.count()
            
            if not sample_data_exists:
                print("📝 No sample quiz data found. Creating sample quantitative and reasoning quizzes...")
                from create_quant_reasoning_data import create_quant_reasoning_data
                create_quant_reasoning_data(force_recreate=False)
            else:
                print(f"✅ Sample quiz data exists. Total: {total_categories} categories, {total_questions} questions, {total_quizzes} quizzes")
        except Exception as e:
            print(f"Note: Could not check/create sample data: {e}")
    
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
    # This starts the built-in Flask development server.
    # 'debug=True' is super helpful for development because it enables an interactive
    # debugger in the browser and automatically reloads the server when you change the code.
    # This should be set to 'False' in a production environment!
    app.run(debug=True, port=5002, host='127.0.0.1')