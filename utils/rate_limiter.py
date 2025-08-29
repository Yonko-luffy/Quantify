# utils/rate_limiter.py
from functools import wraps
from flask import request, render_template, flash
from models.rate_limit import RateLimit


def get_client_ip():
    """Get the real client IP address, considering proxies"""
    if request.headers.getlist("X-Forwarded-For"):
        return request.headers.getlist("X-Forwarded-For")[0].split(',')[0].strip()
    elif request.headers.get("X-Real-IP"):
        return request.headers.get("X-Real-IP")
    else:
        return request.remote_addr


def check_rate_limit(identifier, identifier_type, endpoint):
    """
    Check if an identifier is rate limited
    Returns (is_blocked, status_info)
    """
    status = RateLimit.get_status(identifier, identifier_type, endpoint)
    
    if status['is_blocked']:
        return True, status
    return False, status


def record_attempt(identifier, identifier_type, endpoint, success=False):
    """
    Record an attempt and return detailed status
    Returns (is_now_blocked, status_info)
    """
    is_blocked = RateLimit.record_attempt(identifier, identifier_type, endpoint, success)
    status = RateLimit.get_status(identifier, identifier_type, endpoint)
    
    return is_blocked, status


def get_informative_message(status, identifier_type, identifier=None):
    """
    Generate informative user messages based on rate limit status
    """
    if status['is_blocked']:
        time_left = status['time_remaining_minutes']
        if identifier_type == 'username':
            return f"Account temporarily locked due to too many failed attempts. Try again in {time_left} minute{'s' if time_left != 1 else ''}."
        else:
            return f"Too many failed attempts from your location. Try again in {time_left} minute{'s' if time_left != 1 else ''}."
    else:
        remaining = status['attempts_remaining']
        if remaining <= 2:  # Show warning when close to limit
            return f"Invalid credentials. You have {remaining} attempt{'s' if remaining != 1 else ''} remaining before being temporarily locked."
        else:
            return "Invalid username or password."


def rate_limit_check(endpoint_name, template_name=None, redirect_url=None):
    """
    Decorator to check rate limits before executing a route
    Checks both username (if provided) and IP address
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            client_ip = get_client_ip()
            
            # Check IP-based rate limit first
            is_ip_blocked, ip_status = check_rate_limit(client_ip, 'ip', endpoint_name)
            if is_ip_blocked:
                message = get_informative_message(ip_status, 'ip')
                flash(message, 'error')
                if template_name:
                    return render_template(template_name, 
                                         error=message, 
                                         rate_limit_status=ip_status,
                                         cooldown=True), 429
                else:
                    return "Rate limit exceeded", 429
            
            # Check username-based rate limit (for login attempts)
            if endpoint_name == 'login' and request.method == 'POST':
                username = request.form.get('username') or request.form.get('email')
                if username:
                    is_user_blocked, user_status = check_rate_limit(username, 'username', endpoint_name)
                    if is_user_blocked:
                        message = get_informative_message(user_status, 'username', username)
                        flash(message, 'error')
                        if template_name:
                            return render_template(template_name, 
                                                 error=message,
                                                 rate_limit_status=user_status,
                                                 username=username,
                                                 cooldown=True), 429
                        else:
                            return "Rate limit exceeded", 429
            
            # Proceed with the original function
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def record_login_attempt(username, success=False):
    """
    Helper function to record both username and IP-based login attempts
    Returns (is_blocked, status_info, message)
    """
    client_ip = get_client_ip()
    
    # Record IP-based attempt
    ip_blocked, ip_status = record_attempt(client_ip, 'ip', 'login', success)
    
    # Record username-based attempt
    user_blocked, user_status = record_attempt(username, 'username', 'login', success)
    
    # Return the most restrictive status and appropriate message
    if user_blocked:
        message = get_informative_message(user_status, 'username', username)
        return True, user_status, message
    elif ip_blocked:
        message = get_informative_message(ip_status, 'ip')
        return True, ip_status, message
    else:
        # Not blocked, but provide informative message if attempts are being tracked
        if not success and user_status['attempts_remaining'] <= 2:
            message = get_informative_message(user_status, 'username', username)
            return False, user_status, message
        else:
            return False, user_status, "Invalid username or password."
