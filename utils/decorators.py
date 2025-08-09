# utils/decorators.py
from functools import wraps
from flask import flash, redirect, url_for
from flask_login import login_required, current_user


def admin_required(f):
    """
    Decorator that checks if the current user is logged in and has an 'admin' role.
    This decorator combines login_required with admin role verification.
    """
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not hasattr(current_user, 'role') or current_user.role != 'admin':
            flash("Access denied: Admins only.", "danger")
            return redirect(url_for('quiz.index'))
        return f(*args, **kwargs)
    return decorated_function


def editor_required(f):
    """
    Decorator that checks if the current user is logged in and has 'editor' or 'admin' role.
    """
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not hasattr(current_user, 'role') or current_user.role not in ['editor', 'admin']:
            flash("Access denied: Editor or above privileges required.", "danger")
            return redirect(url_for('quiz.index'))
        return f(*args, **kwargs)
    return decorated_function
