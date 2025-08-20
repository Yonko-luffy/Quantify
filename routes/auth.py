# routes/auth.py - Authentication Routes with CAPTCHA Support and 2FA
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from models import db, Users, OTPCode
from utils.captcha import CaptchaValidator
from utils.email import email_service

# Create blueprint
auth_bp = Blueprint("auth", __name__)

# Initialize limiter for this blueprint
limiter = Limiter(key_func=get_remote_address, default_limits=[])


@auth_bp.route("/signup")
def signup():
    """Display registration form"""
    return render_template("register.html")


@auth_bp.route("/register", methods=["GET", "POST"])
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
            new_user = Users(email=email, username=username, password=hashed_password, role="user")
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for("auth.login", success="Account created successfully! Please log in."))
        
        except Exception as e:
            db.session.rollback()
            return render_template("register.html", error="Registration failed. Please try again!")

    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute,10 per 10 minutes,20 per hour")
def login():
    """Handle user login with CAPTCHA protection and 2FA"""
    success_msg = request.args.get("success")
    
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        captcha_response = request.form.get("g-recaptcha-response")
        
        # Validate CAPTCHA first (if enabled)
        if CaptchaValidator.is_captcha_enabled():
            is_captcha_valid, captcha_error = CaptchaValidator.verify_recaptcha(captcha_response)
            if not is_captcha_valid:
                return render_template("login.html", username=username, error=captcha_error)
        
        # Input validation
        if not username or not password:
            return render_template("login.html", username=username, error="Please enter both username and password.")
        
        # Check user credentials
        user = Users.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            # Check if 2FA is enabled
            if current_app.config.get("TWO_FA_ENABLED", False):
                # Send OTP email
                success, message, otp_code = email_service.send_otp_email(user.email, "login")
                
                if success:
                    # Store user info in session for 2FA verification
                    session['2fa_user_id'] = user.id
                    session['2fa_username'] = user.username
                    flash("Please check your email for the verification code.", "info")
                    return redirect(url_for('auth.verify_2fa'))
                else:
                    return render_template("login.html", username=username, error=f"Failed to send verification code: {message}")
            else:
                # 2FA disabled, login directly
                login_user(user)
                flash("Login successful!", "success")
                
                # Redirect to next page if specified, otherwise to quiz index
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for("quiz.index"))
        else:
            return render_template("login.html", username=username, error="Invalid username or password!")

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
        return render_template("profile.html", error="User not found!")
    
    return render_template("profile.html", user=user, profile_owner=user)


@auth_bp.route("/logout", methods=["GET", "POST"])
@login_required
def logout():
    """Handle user logout"""
    logout_user()
    return redirect(url_for("quiz.index"))


@auth_bp.route("/verify-2fa", methods=["GET", "POST"])
@limiter.limit("3 per minute,10 per hour")
def verify_2fa():
    """Handle 2FA verification"""
    # Check if user is in 2FA process
    if '2fa_user_id' not in session:
        return render_template("login.html", error="Invalid verification session. Please login again.")
    
    if request.method == "POST":
        otp_code = request.form.get("otp_code", "").strip()
        
        if not otp_code:
            return render_template("verify_2fa.html", username=session.get('2fa_username'), error="Please enter the verification code.")
        
        # Get user from session
        user = Users.query.get(session['2fa_user_id'])
        if not user:
            session.pop('2fa_user_id', None)
            session.pop('2fa_username', None)
            return render_template("login.html", error="User not found. Please login again.")
        
        # Verify OTP
        is_valid, message = email_service.verify_otp(user.email, otp_code, 'login')
        
        if is_valid:
            # Clear 2FA session data
            session.pop('2fa_user_id', None)
            session.pop('2fa_username', None)
            
            # Complete login
            login_user(user)
            flash("Login successful!", "success")
            
            # Redirect to next page if specified, otherwise to quiz index
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for("quiz.index"))
        else:
            return render_template("verify_2fa.html", username=session.get('2fa_username'), error=message)
    
    return render_template("verify_2fa.html", username=session.get('2fa_username'))


@auth_bp.route('/forgot-password', methods=["GET", "POST"])
@limiter.limit("3 per 10 minutes,10 per hour")
def forgot_password():
    """Handle forgot password request"""
    if not current_app.config.get('PASSWORD_RESET_ENABLED', False):
        return render_template("login.html", error="Password reset is currently disabled.")
    
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        
        if not email:
            return render_template("forgot_password.html", error="Please enter your email address.")
        
        # Check if user exists
        user = Users.query.filter_by(email=email).first()
        
        if user:
            # Send OTP for password reset
            success, message, otp_code = email_service.send_otp_email(email, 'password_reset')
            
            if success:
                session['reset_email'] = email
                flash("Password reset code sent to your email.", "success")
                return redirect(url_for('auth.verify_reset_otp'))
            else:
                return render_template("forgot_password.html", error=f"Failed to send reset code: {message}")
        else:
            # Don't reveal if email exists or not for security
            flash("If the email exists in our system, you will receive a password reset code.", "info")
    
    return render_template("forgot_password.html")


@auth_bp.route('/verify-reset-otp', methods=["GET", "POST"])
@limiter.limit("3 per minute,10 per hour")
def verify_reset_otp():
    """Verify OTP for password reset"""
    if 'reset_email' not in session:
        return render_template("forgot_password.html", error="Invalid reset session. Please start the password reset process again.")
    
    if request.method == "POST":
        otp_code = request.form.get("otp_code", "").strip()
        
        if not otp_code:
            return render_template("verify_reset_otp.html", error="Please enter the verification code.")
        
        email = session['reset_email']
        
        # Verify OTP
        is_valid, message = email_service.verify_otp(email, otp_code, 'password_reset')
        
        if is_valid:
            session['reset_verified'] = True
            flash("Code verified! Please set your new password.", "success")
            return redirect(url_for('auth.reset_password'))
        else:
            return render_template("verify_reset_otp.html", error=message)
    
    return render_template("verify_reset_otp.html")


@auth_bp.route('/reset-password', methods=["GET", "POST"])
@limiter.limit("3 per minute,5 per hour")
def reset_password():
    """Handle new password setting after OTP verification"""
    if 'reset_email' not in session or not session.get('reset_verified'):
        return render_template("forgot_password.html", error="Invalid reset session. Please start the password reset process again.")
    
    if request.method == "POST":
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        
        # Validation
        if not password or not confirm_password:
            return render_template("reset_password.html", error="Please fill in both password fields.")
        
        if len(password) < 6:
            return render_template("reset_password.html", error="Password must be at least 6 characters long.")
        
        if password != confirm_password:
            return render_template("reset_password.html", error="Passwords do not match.")
        
        # Update user password
        email = session['reset_email']
        user = Users.query.filter_by(email=email).first()
        
        if user:
            try:
                user.password = generate_password_hash(password, method="pbkdf2:sha256")
                db.session.commit()
                
                # Clear session data
                session.pop('reset_email', None)
                session.pop('reset_verified', None)
                
                flash("Password updated successfully! Please login with your new password.", "success")
                return redirect(url_for('auth.login'))
                
            except Exception as e:
                db.session.rollback()
                return render_template("reset_password.html", error="Failed to update password. Please try again.")
        else:
            return render_template("forgot_password.html", error="User not found. Please start the password reset process again.")
    
    return render_template("reset_password.html")


@auth_bp.route('/resend-otp', methods=["POST"])
@limiter.limit("2 per minute,5 per hour")
def resend_otp():
    """Resend OTP for 2FA or password reset"""
    # Check if user is in 2FA process
    if '2fa_user_id' in session:
        user = Users.query.get(session['2fa_user_id'])
        if user:
            success, message, otp_code = email_service.send_otp_email(user.email, 'login')
            if success:
                flash("New verification code sent to your email.", "success")
            else:
                flash(f"Failed to resend code: {message}", "error")
            return redirect(url_for('auth.verify_2fa'))
    
    # Check if user is in password reset process
    elif 'reset_email' in session and not session.get('reset_verified'):
        email = session['reset_email']
        success, message, otp_code = email_service.send_otp_email(email, 'password_reset')
        if success:
            flash("New reset code sent to your email.", "success")
        else:
            flash(f"Failed to resend code: {message}", "error")
        return redirect(url_for('auth.verify_reset_otp'))
    
    flash("Invalid session. Please start the process again.", "error")
    return redirect(url_for('auth.login'))
