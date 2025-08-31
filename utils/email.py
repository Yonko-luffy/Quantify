# utils/email.py
import secrets
from concurrent.futures import ThreadPoolExecutor
from flask import current_app
from flask_mail import Mail, Message
from models import db, OTPCode


class EmailService:
    """
    Service for sending emails and managing OTP codes
    
    IMPLEMENTATION NOTE:
    - Previously, we created a new Thread for every email (inefficient and unmanaged)
    - Now using ThreadPoolExecutor with a fixed pool size for better resource management
    - This is suitable for demo/resume deployment with moderate email volume
    - Future improvement: Implement proper task queue (Celery/RQ) for production scalability
    """
    
    def __init__(self):
        self.mail = None
        # Thread pool for async email sending - limited to 10 concurrent emails
        # This prevents resource exhaustion while allowing reasonable throughput
        self.email_executor = ThreadPoolExecutor(max_workers=10, thread_name_prefix="email-sender")
    
    def init_app(self, app):
        """Initialize Flask-Mail with the app"""
        self.mail = Mail(app)
        
        # Register cleanup function to shutdown thread pool when app closes
        @app.teardown_appcontext
        def shutdown_email_executor(exception):
            # Note: This will be called on every request, so we don't actually shutdown here
            # The thread pool will be cleaned up when the process ends
            pass
    
    def shutdown(self):
        """Properly shutdown the email thread pool"""
        if hasattr(self, 'email_executor'):
            self.email_executor.shutdown(wait=True)
    
    def _email_worker(self, app, msg):
        """
        Worker function that actually sends the email via SMTP
        
        NOTE: This method runs in the ThreadPoolExecutor worker threads
        """
        with app.app_context():
            try:
                self.mail.send(msg)
            except Exception as e:
                # Silent failure for background operation - emails are not critical for app function
                pass
    
    def send_email_async(self, msg):
        """
        Submit email to thread pool for asynchronous sending
        
        IMPROVEMENT NOTE:
        - Old approach: Created new Thread() for each email (resource intensive, no limit)
        - New approach: Submit to thread pool with managed workers
        - Future: Replace with proper task queue (Celery/RQ) for production
        """
        app = current_app._get_current_object()
        # Submit email task to thread pool - returns immediately
        future = self.email_executor.submit(self._email_worker, app, msg)
        return future
    
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
                
                <p>Someone requested to sign in to your Quantify account. Please use the verification code below to complete your login:</p>
                
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
                
                <p>You requested to reset your Quantify password. Please use the verification code below to proceed:</p>
                
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

"""
EMAIL SENDING ARCHITECTURE NOTES:

CURRENT IMPLEMENTATION (ThreadPoolExecutor):
- Uses a fixed thread pool (10 workers) for sending emails asynchronously
- Suitable for demo/resume deployment and moderate email volume (up to ~500 concurrent users)
- Prevents resource exhaustion compared to creating unlimited threads
- Emails are sent in background without blocking web requests

PREVIOUS MISTAKE:
- Initially created a new Thread() for every email request
- This was inefficient and could lead to resource exhaustion
- No limit on concurrent threads, potential for system overload

FUTURE PRODUCTION IMPROVEMENTS:
- Implement proper task queue system (Celery with Redis or RQ)
- Use external email service (SendGrid, Mailgun) for better deliverability
- Add email retry logic and failure handling
- Implement email rate limiting and batching
- Separate email workers from web dynos for better scalability

DEPLOYMENT NOTES:
- Current setup works well for Heroku Basic dyno and demo purposes
- For production with high volume, switch to background job queue
- Monitor email sending performance and adjust thread pool size as needed
"""
