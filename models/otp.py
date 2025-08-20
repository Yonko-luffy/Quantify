# models/otp.py
from datetime import datetime, timedelta
from . import db
from flask import current_app


class OTPCode(db.Model):
    """
    Model for storing temporary OTP codes for 2FA and password reset.
    OTP codes expire after a configurable time period.
    """
    __tablename__ = 'otp_codes'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), nullable=False, index=True)
    otp_code = db.Column(db.String(10), nullable=False)
    purpose = db.Column(db.String(20), nullable=False)  # 'login' or 'password_reset'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)
    
    def __init__(self, email, otp_code, purpose):
        self.email = email
        self.otp_code = otp_code
        self.purpose = purpose
        # Calculate expiry time based on config
        expiry_minutes = current_app.config.get('OTP_EXPIRY_MINUTES', 5)
        self.expires_at = datetime.utcnow() + timedelta(minutes=expiry_minutes)
    
    def is_expired(self):
        """Check if OTP has expired"""
        return datetime.utcnow() > self.expires_at
    
    def is_valid(self, entered_otp):
        """Check if OTP is valid (not expired, not used, and matches)"""
        return (
            not self.used and
            not self.is_expired() and
            self.otp_code == entered_otp
        )
    
    def mark_as_used(self):
        """Mark OTP as used"""
        self.used = True
        db.session.commit()
    
    @classmethod
    def cleanup_expired(cls):
        """Remove expired OTP codes from database"""
        expired_otps = cls.query.filter(cls.expires_at < datetime.utcnow()).all()
        for otp in expired_otps:
            db.session.delete(otp)
        db.session.commit()
        return len(expired_otps)
    
    @classmethod
    def get_valid_otp(cls, email, purpose):
        """Get the most recent valid OTP for an email and purpose"""
        return cls.query.filter_by(
            email=email,
            purpose=purpose,
            used=False
        ).filter(
            cls.expires_at > datetime.utcnow()
        ).order_by(cls.created_at.desc()).first()
    
    def __repr__(self):
        return f'<OTPCode {self.email} - {self.purpose}>'
