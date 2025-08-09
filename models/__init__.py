# models/__init__.py
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()

# Import models after db initialization
from .user import Users
from .quiz import Quiz, Questions, QuizResults, QuizProgress
