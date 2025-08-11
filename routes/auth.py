# routes/auth.py - Authentication Routes with CAPTCHA Support
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from models import db, Users
from utils.captcha import CaptchaValidator

# Create blueprint
auth_bp = Blueprint('auth', __name__)

# Initialize limiter for this blueprint
limiter = Limiter(key_func=get_remote_address, default_limits=[])


@auth_bp.route('/signup')
def signup():
    """Display registration form"""
    return render_template('register.html')


@auth_bp.route('/register', methods=["GET", "POST"])
def register():
    """Handle user registration"""
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        # Validation
        if not username or not email or not password or not confirm_password:
            return render_template("register.html", error="All fields are required!")

        if len(username) < 3:
            return render_template("register.html", error="Username must be at least 3 characters long!")

        if len(password) < 6:
            return render_template("register.html", error="Password must be at least 6 characters long!")

        if password != confirm_password:
            return render_template("register.html", error="Passwords do not match!")

        # Check for existing username/email
        if Users.query.filter_by(username=username).first():
            return render_template("register.html", error="Username already taken!")

        if Users.query.filter_by(email=email).first():
            return render_template("register.html", error="Email already registered!")

        try:
            # Hash password and create user
            hashed_password = generate_password_hash(password, method="pbkdf2:sha256")
            new_user = Users(email=email, username=username, password=hashed_password, role='user')
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for("auth.login", success="Account created successfully! Please log in."))
        
        except Exception as e:
            db.session.rollback()
            return render_template("register.html", error="Registration failed. Please try again!")

    return render_template("register.html")


@auth_bp.route('/login', methods=["GET", "POST"])
@limiter.limit("5 per minute,10 per 10 minutes,20 per hour")  # Enhanced rate limiting
def login():
    """Handle user login with CAPTCHA protection and rate limiting"""
    success_msg = request.args.get('success')
    
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        captcha_response = request.form.get('g-recaptcha-response')
        
        # Validate CAPTCHA first (if enabled)
        if CaptchaValidator.is_captcha_enabled():
            is_captcha_valid, captcha_error = CaptchaValidator.verify_recaptcha(captcha_response)
            if not is_captcha_valid:
                flash(captcha_error, "error")
                return render_template("login.html", username=username)
        
        # Input validation
        if not username or not password:
            flash("Please enter both username and password.", "error")
            return render_template("login.html", username=username)
        
        # Check user credentials
        user = Users.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("Login successful!", "success")
            
            # Redirect to next page if specified, otherwise to quiz index
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for("quiz.index"))
        else:
            flash("Invalid username or password!", "error")
            return render_template("login.html", username=username)

    # If user is already authenticated, redirect to quiz index
    if current_user.is_authenticated:
        return redirect(url_for("quiz.index"))

    return render_template("login.html", success=success_msg)


@auth_bp.route("/profile")
@login_required
def profile():
    """Redirect to current user's profile"""
    return redirect(url_for("auth.profile_user", username=current_user.username))


@auth_bp.route("/profile/<username>")
def profile_user(username):
    # Check if the requested user exists
    user = Users.query.filter_by(username=username).first()
    if not user:
        flash("User not found!", "error")
        return redirect(url_for("quiz.index"))
    
    return render_template("profile.html", user=user, profile_owner=user)


@auth_bp.route('/logout', methods=["GET", "POST"])
@login_required
def logout():
    """Handle user logout"""
    logout_user()
    return redirect(url_for("quiz.index"))
