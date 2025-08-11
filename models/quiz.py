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
