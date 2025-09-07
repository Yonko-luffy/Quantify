# models/quiz.py
from datetime import datetime
from . import db

# Association table for linking Quizzes to their source Categories (Many-to-Many)
quiz_source_categories = db.Table('quiz_source_categories',
    db.Column('quiz_id', db.Integer, db.ForeignKey('quizzes.id'), primary_key=True),
    db.Column('category_id', db.Integer, db.ForeignKey('categories.id'), primary_key=True)
)

# Association table for linking a QuizAttempt to its specific Questions (Many-to-Many)
attempt_questions = db.Table('attempt_questions',
    db.Column('attempt_id', db.Integer, db.ForeignKey('quiz_attempts.id'), primary_key=True),
    db.Column('question_id', db.Integer, db.ForeignKey('questions.id'), primary_key=True)
)

class Category(db.Model):
    """
    Organizes all questions into a structured, hierarchical question bank.
    """
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    
    parent = db.relationship('Category', remote_side=[id], backref='sub_categories')
    
    def __repr__(self):
        return f'<Category {self.name}>'

class Question(db.Model):
    """
    Represents an individual question in the question bank, linked to a Category.
    """
    __tablename__ = 'questions'
    
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    question_image_url = db.Column(db.String(255), nullable=True)
    
    # Options stored as JSON to support text and images
    # Format: [{"text": "Option A", "image_url": "..."}, ...]
    options = db.Column(db.JSON, nullable=False)
    
    # Supports multiple correct answers as array of indices
    correct_answers = db.Column(db.ARRAY(db.Integer), nullable=False)
    explanation = db.Column(db.Text, nullable=True)
    
    category = db.relationship('Category', backref=db.backref('questions', lazy='dynamic'))

    def __repr__(self):
        return f'<Question {self.question_text[:50]}...>'

class Quiz(db.Model):
    """
    A template or set of rules for generating a quiz from one or more categories.
    """
    __tablename__ = 'quizzes'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    quiz_type = db.Column(db.String(50), nullable=False, default='standard', index=True)
    number_of_questions = db.Column(db.Integer, nullable=False, default=10)
    time_limit_minutes = db.Column(db.Integer, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_archive = db.Column(db.Boolean, nullable=False, default=False, index=True)

    # Many-to-Many relationship with Categories
    source_categories = db.relationship('Category', secondary=quiz_source_categories, lazy='subquery',
                                       backref=db.backref('quizzes', lazy=True))
    creator = db.relationship('Users', backref=db.backref('created_quizzes', lazy=True))
    
    def __repr__(self):
        return f'<Quiz {self.name}>'

class QuizAttempt(db.Model):
    """
    Represents a user's single, unique attempt at a quiz, with a set of questions.
    """
    __tablename__ = 'quiz_attempts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='in_progress')  # in_progress, completed
    score = db.Column(db.Integer, nullable=False, default=0)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    user = db.relationship('Users', backref=db.backref('quiz_attempts', lazy=True))
    quiz_template = db.relationship('Quiz', backref=db.backref('attempts', lazy=True))
    
    # Many-to-Many relationship with Questions for this specific attempt
    questions = db.relationship('Question', secondary=attempt_questions, lazy='subquery',
                                  backref=db.backref('attempts', lazy=True))
    
    def __repr__(self):
        return f'<QuizAttempt user_id={self.user_id} quiz_id={self.quiz_id} status={self.status}>'
    
    def is_completed(self):
        """Check if the quiz attempt has been completed"""
        return self.status == 'completed'
    
    def get_completion_percentage(self):
        """Calculate completion percentage based on answered questions"""
        if not self.questions:
            return 0
        total_questions = len(self.questions)
        if total_questions == 0:
            return 100
        
        # Count answered questions for this attempt
        from . import QuizResult  # Import here to avoid circular imports
        answered = QuizResult.query.filter_by(attempt_id=self.id).count()
        return min(100, (answered / total_questions) * 100)

class QuizResult(db.Model):
    """
    Stores a user's answer to a single question for a specific attempt.
    """
    __tablename__ = 'quiz_results'
    
    id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(db.Integer, db.ForeignKey('quiz_attempts.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    
    # Stores multiple selected answers as array of indices
    selected_answers = db.Column(db.ARRAY(db.Integer), nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False)
    answered_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    attempt = db.relationship('QuizAttempt', backref=db.backref('results', lazy=True))
    user = db.relationship('Users', backref=db.backref('all_quiz_results', lazy=True))
    question = db.relationship('Question', backref=db.backref('results', lazy=True))
    
    def __repr__(self):
        return f'<QuizResult attempt_id={self.attempt_id} question_id={self.question_id} correct={self.is_correct}>'


# Legacy models for backward compatibility during migration
# These will be removed after data migration is complete
class LegacyQuiz(db.Model):
    """Legacy Quiz model - will be removed after migration"""
    __tablename__ = 'legacy_quizzes'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class LegacyQuestion(db.Model):
    """Legacy Question model - will be removed after migration"""
    __tablename__ = 'legacy_questions'
    
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('legacy_quizzes.id'), nullable=False)
    question_text = db.Column(db.String(500), nullable=False)
    options = db.Column(db.ARRAY(db.String(255)), nullable=False)
    answer_index = db.Column(db.Integer, nullable=False)
    explanation = db.Column(db.Text, nullable=True)