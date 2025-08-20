# utils/email.py
import secrets
from flask import current_app
from flask_mail import Mail, Message
from models import db, OTPCode
from threading import Thread


class EmailService:
    """Service for sending emails and managing OTP codes"""
    
    def __init__(self):
        self.mail = None
    
    def init_app(self, app):
        """Initialize Flask-Mail with the app"""
        self.mail = Mail(app)
    
    def _send_async_email(self, app, msg):
        """Send email in background thread"""
        with app.app_context():
            try:
                self.mail.send(msg)
            except Exception as e:
                pass  # Silent failure for background operation
    
    def send_email_async(self, msg):
        """Send email asynchronously"""
        app = current_app._get_current_object()
        thread = Thread(target=self._send_async_email, args=[app, msg])
        thread.start()
        return thread
    
    @staticmethod
    def generate_otp(length=None):
        """Generate a random numeric OTP"""
        if length is None:
            length = current_app.config.get('OTP_LENGTH', 6)
        return ''.join([str(secrets.randbelow(10)) for _ in range(length)])
    
    def send_otp_email(self, email, purpose='login'):
        """
        Generate and send OTP email for login or password reset
        Returns: (success: bool, message: str, otp_code: str or None)
        """
        try:
            # Check if email and mail service are configured
            if not self.mail:
                return False, "Email service not configured", None
            
            if not current_app.config.get('MAIL_USERNAME'):
                return False, "Email configuration incomplete", None
            
            # Generate OTP
            otp_code = self.generate_otp()
            
            # Clean up old OTPs for this email and purpose
            old_otps = OTPCode.query.filter_by(email=email, purpose=purpose, used=False).all()
            for old_otp in old_otps:
                db.session.delete(old_otp)
            
            # Create new OTP record
            otp_record = OTPCode(email=email, otp_code=otp_code, purpose=purpose)
            db.session.add(otp_record)
            db.session.commit()
            
            # Prepare email content
            if purpose == 'login':
                subject = "Your Login Verification Code"
                template = self._get_login_email_template(otp_code)
            else:  # password_reset
                subject = "Your Password Reset Code"
                template = self._get_password_reset_email_template(otp_code)
            
            # Send email
            msg = Message(
                subject=subject,
                recipients=[email],
                html=template,
                sender=current_app.config.get('MAIL_DEFAULT_SENDER')
            )
            
            # Send email asynchronously - NO WAITING!
            self.send_email_async(msg)
            return True, "OTP sent successfully", otp_code
            
        except Exception as e:
            return False, "Failed to send email", None
    
    def verify_otp(self, email, entered_otp, purpose='login'):
        """
        Verify OTP code
        Returns: (valid: bool, message: str)
        """
        try:
            # Find valid OTP
            otp_record = OTPCode.get_valid_otp(email, purpose)
            
            if not otp_record:
                return False, "Invalid or expired OTP code"
            
            if otp_record.is_valid(entered_otp):
                otp_record.mark_as_used()
                return True, "OTP verified successfully"
            else:
                return False, "Invalid OTP code"
                
        except Exception as e:
            return False, "OTP verification failed"
    
    @staticmethod
    def _get_login_email_template(otp_code):
        """HTML template for login OTP email"""
        expiry_minutes = current_app.config.get('OTP_EXPIRY_MINUTES', 5)
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f4f4f4; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
                .header {{ text-align: center; color: #333; margin-bottom: 30px; }}
                .otp-code {{ font-size: 36px; font-weight: bold; color: #007bff; text-align: center; padding: 20px; background: #f8f9fa; border-radius: 5px; margin: 20px 0; letter-spacing: 5px; }}
                .info {{ color: #666; text-align: center; margin: 20px 0; }}
                .warning {{ color: #dc3545; text-align: center; font-size: 14px; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔐 Login Verification</h1>
                </div>
                
                <p>Hello,</p>
                
                <p>Someone requested to sign in to your Quiz App account. Please use the verification code below to complete your login:</p>
                
                <div class="otp-code">{otp_code}</div>
                
                <div class="info">
                    <p>This code will expire in <strong>{expiry_minutes} minutes</strong>.</p>
                    <p>If you didn't request this login, please ignore this email.</p>
                </div>
                
                <div class="warning">
                    <p>⚠️ Never share this code with anyone. Our team will never ask for this code.</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    @staticmethod
    def _get_password_reset_email_template(otp_code):
        """HTML template for password reset OTP email"""
        expiry_minutes = current_app.config.get('OTP_EXPIRY_MINUTES', 5)
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f4f4f4; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
                .header {{ text-align: center; color: #333; margin-bottom: 30px; }}
                .otp-code {{ font-size: 36px; font-weight: bold; color: #dc3545; text-align: center; padding: 20px; background: #f8f9fa; border-radius: 5px; margin: 20px 0; letter-spacing: 5px; }}
                .info {{ color: #666; text-align: center; margin: 20px 0; }}
                .warning {{ color: #dc3545; text-align: center; font-size: 14px; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔑 Password Reset Request</h1>
                </div>
                
                <p>Hello,</p>
                
                <p>You requested to reset your Quiz App password. Please use the verification code below to proceed:</p>
                
                <div class="otp-code">{otp_code}</div>
                
                <div class="info">
                    <p>This code will expire in <strong>{expiry_minutes} minutes</strong>.</p>
                    <p>If you didn't request this password reset, please ignore this email and your password will remain unchanged.</p>
                </div>
                
                <div class="warning">
                    <p>⚠️ Never share this code with anyone. Our team will never ask for this code.</p>
                </div>
            </div>
        </body>
        </html>
        """


# Global email service instance
email_service = EmailService()
