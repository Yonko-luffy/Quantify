# models/quiz.py
from datetime import datetime
from . import db


class Quiz(db.Model):
    """
    Quiz model representing a collection of questions.
    Each quiz is created by a user.
    """
    __tablename__ = 'quizzes'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    creator = db.relationship('Users', backref=db.backref('created_quizzes', lazy=True))
    
    def __repr__(self):
        return f'<Quiz {self.name}>'


class Questions(db.Model):
    """
    Question model representing individual questions within a quiz.
    Each question has multiple choice options and a correct answer index.
    """
    __tablename__ = 'questions'
    
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    question_text = db.Column(db.String(500), nullable=False)
    options = db.Column(db.ARRAY(db.String(255)), nullable=False)
    answer_index = db.Column(db.Integer, nullable=False)  # Index of the correct answer in options
    explanation = db.Column(db.Text, nullable=True)  # Explanation for why the answer is correct

    # Relationship to Quiz with cascade delete
    quiz = db.relationship('Quiz', backref=db.backref('questions', lazy=True, cascade="all, delete-orphan"))
    
    def __repr__(self):
        return f'<Question {self.question_text[:50]}...>'
    
    def get_correct_answer(self):
        """Get the correct answer text"""
        if 0 <= self.answer_index < len(self.options):
            return self.options[self.answer_index]
        return None


class QuizResults(db.Model):
    """
    Quiz result model storing individual question answers from users.
    Tracks whether each answer was correct and when it was submitted.
    Supports multiple attempts with attempt_number tracking.
    """
    __tablename__ = 'quiz_results'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    selected_index = db.Column(db.Integer, nullable=False)  # Index of the user's selected answer
    is_correct = db.Column(db.Boolean, nullable=False)
    attempt_number = db.Column(db.Integer, nullable=False, default=1)  # Track attempt number
    answered_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('Users', backref=db.backref('quiz_results', lazy=True))
    quiz = db.relationship('Quiz', backref=db.backref('results', lazy=True))
    question = db.relationship('Questions', backref=db.backref('results', lazy=True))
    
    def __repr__(self):
        return f'<QuizResult user_id={self.user_id} quiz_id={self.quiz_id} attempt={self.attempt_number} correct={self.is_correct}>'


class QuizProgress(db.Model):
    """
    Quiz progress model tracking a user's journey through a quiz.
    Stores current position, score, and completion status.
    Supports multiple attempts with attempt_number tracking.
    """
    __tablename__ = 'quiz_progress'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    last_question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=True)
    score = db.Column(db.Integer, nullable=False, default=0)
    attempt_number = db.Column(db.Integer, nullable=False, default=1)  # Track attempt number
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    user = db.relationship('Users', backref=db.backref('quiz_progress', lazy=True))
    quiz = db.relationship('Quiz', backref=db.backref('progress', lazy=True))
    last_question = db.relationship('Questions', backref=db.backref('progress', lazy=True))
    
    def __repr__(self):
        return f'<QuizProgress user_id={self.user_id} quiz_id={self.quiz_id} attempt={self.attempt_number} score={self.score}>'
    
    def is_completed(self):
        """Check if the quiz has been completed"""
        return self.completed_at is not None
    
    def get_completion_percentage(self):
        """Calculate completion percentage based on total questions"""
        if not self.quiz or not self.quiz.questions:
            return 0
        total_questions = len(self.quiz.questions)
        if total_questions == 0:
            return 100
        # Count answered questions
        answered = QuizResults.query.filter_by(
            user_id=self.user_id,
            quiz_id=self.quiz_id
        ).count()
        return min(100, (answered / total_questions) * 100)

# # ==============================================================================
# # NEW, SCALABLE SCHEMA FOR A DYNAMIC QUIZ PLATFORM
# # ==============================================================================

# class Category(db.Model):
#     """
#     NEW MODEL: Organizes all questions into a structured question bank.
#     This is the core of your randomization feature.
#     """
#     __tablename__ = 'categories'
    
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(100), unique=True, nullable=False)
#     # Allows for sub-categories, e.g., Quant -> Algebra -> Equations
#     parent_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    
#     # Relationships
#     parent = db.relationship('Category', remote_side=[id], backref='sub_categories')
    
#     def __repr__(self):
#         return f'<Category {self.name}>'


# class Question(db.Model):
#     """
#     Represents an individual question in the question bank.
#     --- MAJOR CHANGE: Now linked to a Category and supports images. ---
#     """
#     __tablename__ = 'questions'
    
#     id = db.Column(db.Integer, primary_key=True)
    
#     # --- CHANGE: Foreign key is now to a Category ---
#     category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    
#     question_text = db.Column(db.Text, nullable=False)
#     question_image_url = db.Column(db.String(255), nullable=True) 

#     # --- CHANGE: Options are now JSON to support text and images ---
#     # Stored as [{"text": "Option A", "image_url": "..."}, ...]
#     options = db.Column(db.JSON, nullable=False)
    
#     # --- CHANGE: Supports multiple correct answers ---
#     # Stores correct answers as an array of indices, e.g., [0] or [1, 3]
#     correct_answers = db.Column(db.ARRAY(db.Integer), nullable=False)
#     explanation = db.Column(db.Text, nullable=True)
    
#     # Relationships
#     category = db.relationship('Category', backref=db.backref('questions', lazy='dynamic'))

#     def __repr__(self):
#         return f'<Question {self.question_text[:50]}...>'


# class Quiz(db.Model):
#     """
#     REDEFINED MODEL: This is now a TEMPLATE or a set of rules for a quiz.
#     It no longer holds questions directly.
#     """
#     __tablename__ = 'quizzes'
    
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(150), nullable=False)
#     description = db.Column(db.Text, nullable=True)
    
#     # Defines the type, e.g., 'Community Weekly', 'Quant Practice', 'Custom User Test'
#     quiz_type = db.Column(db.String(50), nullable=False, default='standard', index=True)
    
#     # --- NEW: These fields define how to build the quiz ---
#     # The category to pull questions from (can be null for a mix)
#     source_category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
#     number_of_questions = db.Column(db.Integer, nullable=False, default=10)
#     time_limit_minutes = db.Column(db.Integer, nullable=True)
    
#     created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
#     # Relationships
#     source_category = db.relationship('Category')
#     creator = db.relationship('Users', backref=db.backref('created_quizzes', lazy=True))


# # Association table to link a specific attempt with its specific set of questions
# attempt_questions = db.Table('attempt_questions',
#     db.Column('attempt_id', db.Integer, db.ForeignKey('quiz_attempts.id'), primary_key=True),
#     db.Column('question_id', db.Integer, db.ForeignKey('questions.id'), primary_key=True)
# )


# class QuizAttempt(db.Model):
#     """
#     NEW MODEL: Represents a user's single, unique attempt at a quiz.
#     This is the "session" that holds the randomized questions.
#     This model effectively replaces the old 'QuizProgress'.
#     """
#     __tablename__ = 'quiz_attempts'

#     id = db.Column(db.Integer, primary_key=True)
#     user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
#     quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False) # The template used
    
#     status = db.Column(db.String(20), nullable=False, default='in_progress') # in_progress, completed
#     score = db.Column(db.Integer, nullable=False, default=0)
#     started_at = db.Column(db.DateTime, default=datetime.utcnow)
#     completed_at = db.Column(db.DateTime, nullable=True)
    
#     # Relationships
#     user = db.relationship('Users', backref=db.backref('quiz_attempts', lazy=True))
#     quiz_template = db.relationship('Quiz', backref=db.backref('attempts', lazy=True))
    
#     # This is the list of randomly selected questions for this specific attempt
#     questions = db.relationship('Question', secondary=attempt_questions, lazy='subquery',
#                                 backref=db.backref('attempts', lazy=True))


# class QuizResult(db.Model):
#     """
#     Stores a user's answer to a single question for a specific attempt.
#     --- MAJOR CHANGE: Linked to a QuizAttempt and supports multiple answers. ---
#     """
#     __tablename__ = 'quiz_results'
    
#     id = db.Column(db.Integer, primary_key=True)
#     # --- CHANGE: Now linked to the unique attempt ---
#     attempt_id = db.Column(db.Integer, db.ForeignKey('quiz_attempts.id'), nullable=False)
    
#     user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
#     question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    
#     # --- CHANGE: Stores multiple selected answers ---
#     # Stores the answer(s) the user selected, e.g., [1] or [0, 2]
#     selected_answers = db.Column(db.ARRAY(db.Integer), nullable=False)
#     is_correct = db.Column(db.Boolean, nullable=False)
    
#     # Relationships
#     attempt = db.relationship('QuizAttempt', backref=db.backref('results', lazy=True))