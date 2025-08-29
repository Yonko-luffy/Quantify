# models/rate_limit.py
from datetime import datetime, timedelta
from . import db


class RateLimit(db.Model):
    """
    Simple rate limiting model to track login attempts and blocks.
    Tracks both username-based and IP-based attempts for dual protection.
    """
    __tablename__ = 'rate_limits'
    
    id = db.Column(db.Integer, primary_key=True)
    identifier = db.Column(db.String(150), nullable=False)  # username OR ip_address
    identifier_type = db.Column(db.String(20), nullable=False)  # 'username' or 'ip'
    endpoint = db.Column(db.String(50), nullable=False)  # 'login', 'forgot_password', etc.
    attempt_count = db.Column(db.Integer, default=1)
    first_attempt = db.Column(db.DateTime, default=datetime.utcnow)
    last_attempt = db.Column(db.DateTime, default=datetime.utcnow)
    blocked_until = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<RateLimit {self.identifier_type}:{self.identifier} {self.endpoint}>'
    
    @classmethod
    def cleanup_old_records(cls, hours_old=24):
        """Remove rate limit records older than specified hours"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_old)
        old_records = cls.query.filter(cls.last_attempt < cutoff_time).all()
        for record in old_records:
            db.session.delete(record)
        db.session.commit()
        return len(old_records)
    
    @classmethod
    def is_blocked(cls, identifier, identifier_type, endpoint):
        """Check if an identifier is currently blocked"""
        record = cls.query.filter_by(
            identifier=identifier,
            identifier_type=identifier_type,
            endpoint=endpoint
        ).first()
        
        if not record or not record.blocked_until:
            return False
            
        # Check if block has expired
        if datetime.utcnow() > record.blocked_until:
            record.blocked_until = None
            record.attempt_count = 0
            db.session.commit()
            return False
            
        return True
    
    @classmethod
    def get_status(cls, identifier, identifier_type, endpoint):
        """
        Get detailed status for an identifier
        Returns: {
            'is_blocked': bool,
            'attempts_used': int,
            'attempts_remaining': int,
            'total_attempts_allowed': int,
            'blocked_until': datetime or None,
            'time_remaining': timedelta or None,
            'time_remaining_minutes': int or None
        }
        """
        record = cls.query.filter_by(
            identifier=identifier,
            identifier_type=identifier_type,
            endpoint=endpoint
        ).first()
        
        limit = cls._get_limit_for_endpoint(endpoint)
        current_time = datetime.utcnow()
        
        # Default status for new users
        if not record:
            return {
                'is_blocked': False,
                'attempts_used': 0,
                'attempts_remaining': limit,
                'total_attempts_allowed': limit,
                'blocked_until': None,
                'time_remaining': None,
                'time_remaining_minutes': None
            }
        
        # Check if block has expired
        is_blocked = False
        time_remaining = None
        time_remaining_minutes = None
        
        if record.blocked_until and current_time < record.blocked_until:
            is_blocked = True
            time_remaining = record.blocked_until - current_time
            time_remaining_minutes = int(time_remaining.total_seconds() / 60) + 1  # Round up
        elif record.blocked_until and current_time >= record.blocked_until:
            # Block expired, reset
            record.blocked_until = None
            record.attempt_count = 0
            db.session.commit()
        
        # Check if we're still in the time window
        time_window = timedelta(minutes=15)
        if record.first_attempt and current_time - record.first_attempt > time_window:
            # Time window expired, reset attempts
            attempts_used = 0
        else:
            attempts_used = record.attempt_count
        
        return {
            'is_blocked': is_blocked,
            'attempts_used': attempts_used,
            'attempts_remaining': max(0, limit - attempts_used),
            'total_attempts_allowed': limit,
            'blocked_until': record.blocked_until,
            'time_remaining': time_remaining,
            'time_remaining_minutes': time_remaining_minutes
        }
    
    @classmethod
    def record_attempt(cls, identifier, identifier_type, endpoint, success=False):
        """Record a login attempt and check if should be blocked"""
        # Clean up old records periodically (1% chance per call)
        import random
        if random.randint(1, 100) == 1:
            cls.cleanup_old_records()
        
        # Find existing record
        record = cls.query.filter_by(
            identifier=identifier,
            identifier_type=identifier_type,
            endpoint=endpoint
        ).first()
        
        # If successful attempt, reset the counter
        if success:
            if record:
                db.session.delete(record)
                db.session.commit()
            return False
        
        # Handle failed attempt
        time_window = timedelta(minutes=15)  # 15-minute window
        current_time = datetime.utcnow()
        
        if not record:
            # Create new record
            record = cls(
                identifier=identifier,
                identifier_type=identifier_type,
                endpoint=endpoint,
                attempt_count=1,
                first_attempt=current_time,
                last_attempt=current_time
            )
            db.session.add(record)
        else:
            # Check if we're still in the time window
            if current_time - record.first_attempt > time_window:
                # Reset the window
                record.attempt_count = 1
                record.first_attempt = current_time
                record.last_attempt = current_time
                record.blocked_until = None
            else:
                # Increment attempt count
                record.attempt_count += 1
                record.last_attempt = current_time
        
        # Check if should be blocked
        limit = cls._get_limit_for_endpoint(endpoint)
        if record.attempt_count >= limit:
            block_duration = cls._get_block_duration_for_endpoint(endpoint)
            record.blocked_until = current_time + block_duration
        
        db.session.commit()
        return record.blocked_until is not None
    
    @classmethod
    def _get_limit_for_endpoint(cls, endpoint):
        """Get attempt limit for specific endpoint"""
        limits = {
            'login': 5,
            'forgot_password': 3,
            'reset_password': 3,
            'verify_2fa': 3,
            'register': 5
        }
        return limits.get(endpoint, 5)
    
    @classmethod
    def _get_block_duration_for_endpoint(cls, endpoint):
        """Get block duration for specific endpoint"""
        durations = {
            'login': timedelta(minutes=30),
            'forgot_password': timedelta(hours=1),
            'reset_password': timedelta(hours=1),
            'verify_2fa': timedelta(minutes=15),
            'register': timedelta(minutes=30)
        }
        return durations.get(endpoint, timedelta(minutes=30))
