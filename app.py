# app.py - Modular Flask Application
from flask import Flask, render_template, request
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_limiter.errors import RateLimitExceeded
from flask_wtf.csrf import CSRFProtect
from livereload import Server

# Import configuration
from config import Config

# Import models and database
from models import db, login_manager, Users

# Import route blueprints
from routes import auth_bp, admin_bp, quiz_bp

# ================================
# App & Config Setup
# ================================
app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions with app
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

# CSRF Protection (recommended with CAPTCHA)
csrf = CSRFProtect(app)

# Limiter setup
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=[]
)

# ================================
# Template Context Processors
# ================================
@app.context_processor
def inject_recaptcha_config():
    """Make reCAPTCHA configuration available in all templates"""
    return {
        'RECAPTCHA_PUBLIC_KEY': app.config.get('RECAPTCHA_PUBLIC_KEY'),
        'RECAPTCHA_ENABLED': app.config.get('RECAPTCHA_ENABLED', False),
        'RECAPTCHA_OPTIONS': app.config.get('RECAPTCHA_OPTIONS', {})
    }

# ================================
# Error Handlers
# ================================
@app.errorhandler(RateLimitExceeded)
def handle_rate_limit(e):
    """Handle rate limit exceeded errors with CAPTCHA support"""
    cooldown = True
    return render_template("login.html", 
                         error="Too many login attempts. Please complete CAPTCHA and try again.", 
                         cooldown=cooldown), 429

# ================================
# Login Manager User Loader
# ================================
@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for login manager"""
    return db.session.get(Users, int(user_id))

# ================================
# Register Blueprints
# ================================
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(quiz_bp)

# ================================
# Database Initialization
# ================================
with app.app_context():
    db.create_all()
    print("✅ Database tables created successfully.")

# ================================
# Development Server
# ================================
if __name__ == "__main__":
    # Use standard Flask development server with debug mode
    app.run(debug=True, port=5002, host='127.0.0.1')
    
    # Start the Livereload server on a different port
    # server = Server(app.wsgi_app)
    # server.serve(port=5001, host='127.0.0.1')
