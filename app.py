# ==============================================================================
# app.py - Main Application File
# Description: Initializes the Flask application, configures extensions,
#              registers blueprints, and sets up error handlers.
# ==============================================================================

# --- Core Flask Imports ---
# We're importing the main Flask class to create our application instance,
# and render_template to serve HTML files to the user.
from flask import Flask, render_template

# --- Extensions ---
# These are add-ons for Flask that provide extra functionality.
from flask_limiter import Limiter                      # For rate-limiting requests to prevent abuse.
from flask_limiter.util import get_remote_address      # A helper function to get the user's IP address for rate-limiting.
from flask_limiter.errors import RateLimitExceeded      # The specific exception raised when a rate limit is hit.
from flask_wtf.csrf import CSRFProtect                  # Provides Cross-Site Request Forgery (CSRF) protection for our forms.

# --- Local Imports ---
# Here, we're bringing in our own code from other files in the project.
from config import Config                               # Imports the application configuration class from config.py.
from models import db, login_manager, Users             # Imports the database instance, login manager, and our User model.
from routes import auth_bp, admin_bp, quiz_bp           # Imports route blueprints for modular routing. This keeps our app organized.
from utils.email import email_service                   # Import email service for OTP functionality

# ==============================================================================
# Application Setup & Configuration
# ==============================================================================

# Initialize the core Flask application.
# '__name__' is a special Python variable that gives Flask the path to the current module.
# This helps Flask find resources like templates and static files.
app = Flask(__name__)

# Load configuration settings from the Config object we imported from config.py.
# This is great practice because it keeps our secret keys and settings
# separate from our application logic.
app.config.from_object(Config)

# ==============================================================================
# Initialize Extensions
# ==============================================================================

# Now we'll connect the extensions we imported to our Flask app instance.
# The 'init_app' pattern is used to bind an extension to a specific app.
db.init_app(app)
login_manager.init_app(app)
email_service.init_app(app)  # Initialize email service for OTP functionality

# This tells Flask-Login where to redirect users if they try to access a page
# that requires them to be logged in. 'auth.login' refers to the 'login' function
# inside the 'auth_bp' blueprint.
login_manager.login_view = 'auth.login'

# Initialize CSRF protection for the entire application.
# This will automatically add a hidden CSRF token to our forms to prevent malicious attacks.
csrf = CSRFProtect(app)

# Initialize the rate limiter to protect our app from brute-force attacks or scraping.
limiter = Limiter(
    app=app,
    # We use 'get_remote_address' to identify users by their IP address.
    # This means limits are applied on a per-IP basis.
    key_func=get_remote_address,
    # We're setting the default limits to empty because we'll apply specific limits
    # directly to the routes that need them (like the login route) using decorators.
    default_limits=[]
)

# ==============================================================================
# Template Context Processor
# ==============================================================================

# A context processor is a Flask feature that runs before a template is rendered.
# It's used to inject variables automatically into the context of every template.
@app.context_processor
def inject_recaptcha_config():
    """
    Injects reCAPTCHA configuration into all Jinja2 templates.
    This is super useful because it makes the public key and other settings
    globally available in the front-end without having to pass them from
    every single route that renders a template. It keeps our route functions clean.
    """
    # This dictionary will be available in all our templates.
    # For example, in a template, we can now just use {{ RECAPTCHA_PUBLIC_KEY }}.
    return {
        'RECAPTCHA_PUBLIC_KEY': app.config.get('RECAPTCHA_PUBLIC_KEY'),
        'RECAPTCHA_ENABLED': app.config.get('RECAPTCHA_ENABLED', False),
        'RECAPTCHA_OPTIONS': app.config.get('RECAPTCHA_OPTIONS', {})
    }

# ==============================================================================
# Error Handlers
# ==============================================================================

# This decorator registers a custom function to handle a specific error type.
# In this case, we're creating a friendly response for when a user hits our rate limit.
@app.errorhandler(RateLimitExceeded)
def handle_rate_limit(e):
    """
    Custom error page for users who exceed the request rate limit.
    Instead of showing a generic server error, we render the login page again
    but with a specific error message, letting the user know what happened.
    The 429 status code means "Too Many Requests".
    """
    cooldown = True # A flag we can use in the template to show a CAPTCHA or other UI element.
    return render_template("login.html",
                           error="Too many login attempts. Please complete CAPTCHA and try again.",
                           cooldown=cooldown), 429

# ==============================================================================
# User Loader for Flask-Login
# ==============================================================================

# This is a required function for Flask-Login. It's used to reload the user
# object from the user ID stored in the session cookie.
@login_manager.user_loader
def load_user(user_id):
    """
    Flask-Login calls this function on every request for a logged-in user
    to get the current user object. It takes the user ID from the session
    and uses it to query the database.
    """
    # 'db.session.get' is an efficient way to fetch an object by its primary key.
    return db.session.get(Users, int(user_id))

# ==============================================================================
# Register Route Blueprints
# ==============================================================================

# Blueprints are Flask's way of organizing an application into smaller, reusable parts.
# Instead of having all our routes in this one file, we've split them into logical
# groups (authentication, admin, quiz) and now we're registering them with the app.
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(quiz_bp)

# ==============================================================================
# Database Initialization
# ==============================================================================

# The 'app_context' is necessary here because SQLAlchemy needs to know about the
# application's configuration (like the database URI) to connect to the database.
with app.app_context():
    # This command looks at all the models we've defined (like the 'Users' model)
    # and creates the corresponding tables in the database if they don't already exist.
    # It's safe to run this every time the app starts.
    db.create_all()

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