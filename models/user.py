# models/user.py
from flask_login import UserMixin
from . import db


class Users(db.Model, UserMixin):
    """
    User model for authentication and authorization.
    Includes role-based access control with support for 'user', 'editor', and 'admin' roles.
    """
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')  # 'user', 'editor', 'admin'
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def is_admin(self):
        """Check if user has admin role"""
        return self.role == 'admin'
    
    def is_editor(self):
        """Check if user has editor role or higher"""
        return self.role in ['editor', 'admin']
