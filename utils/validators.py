# utils/validators.py
from flask import flash
import re
from models import Quiz, Questions, QuizResults, QuizProgress

class QuizValidator:
    """Comprehensive quiz validation utility"""
    
    @staticmethod
    def validate_quiz_data(quiz_name):
        """Validate quiz creation/edit data"""
        errors = []
        
        # Quiz name validation
        if not quiz_name:
            errors.append("Quiz name is required")
        elif len(quiz_name.strip()) < 3:
            errors.append("Quiz name must be at least 3 characters long")
        elif len(quiz_name.strip()) > 150:
            errors.append("Quiz name cannot exceed 150 characters")
        elif not re.match(r'^[a-zA-Z0-9\s\-_.,!?()]+$', quiz_name.strip()):
            errors.append("Quiz name contains invalid characters")
        
        return errors
    
    @staticmethod
    def validate_question_data(question_text, options, answer_index):
        """Validate question creation/edit data"""
        errors = []
        
        # Question text validation
        if not question_text:
            errors.append("Question text is required")
        elif len(question_text.strip()) < 10:
            errors.append("Question must be at least 10 characters long")
        elif len(question_text.strip()) > 500:
            errors.append("Question cannot exceed 500 characters")
        
        # Options validation
        if not options or len(options) < 2:
            errors.append("At least 2 answer options are required")
        elif len(options) > 6:
            errors.append("Maximum 6 answer options allowed")
        else:
            # Validate each option
            valid_options = []
            for i, option in enumerate(options):
                if not option or not option.strip():
                    errors.append(f"Option {i+1} cannot be empty")
                elif len(option.strip()) > 255:
                    errors.append(f"Option {i+1} cannot exceed 255 characters")
                else:
                    valid_options.append(option.strip())
            
            # Check for duplicate options
            if len(set(valid_options)) != len(valid_options):
                errors.append("Answer options must be unique")
        
        # Answer index validation
        if answer_index is None:
            errors.append("Correct answer must be selected")
        elif not isinstance(answer_index, int):
            try:
                answer_index = int(answer_index)
            except (ValueError, TypeError):
                errors.append("Invalid answer selection")
        
        if isinstance(answer_index, int) and options:
            if answer_index < 0 or answer_index >= len(options):
                errors.append("Selected answer is out of range")
        
        return errors
    
    @staticmethod
    def validate_answer_submission(quiz_id, question_id, selected_index, user_id):
        """Validate individual answer submission"""
        errors = []
        
        # Basic validation
        if not quiz_id:
            errors.append("Quiz ID is required")
        if not question_id:
            errors.append("Question ID is required")
        if selected_index is None:
            errors.append("Answer selection is required")
        
        # Check if question belongs to quiz
        question = Questions.query.filter_by(id=question_id, quiz_id=quiz_id).first()
        if not question:
            errors.append("Question not found in this quiz")
            return errors
        
        # Validate selected index
        try:
            selected_index = int(selected_index)
            if selected_index < 0 or selected_index >= len(question.options):
                errors.append("Invalid answer selection")
        except (ValueError, TypeError):
            errors.append("Invalid answer format")
        
        # Get current attempt number
        current_progress = QuizProgress.query.filter_by(
            user_id=user_id,
            quiz_id=quiz_id,
            completed_at=None
        ).first()
        
        if not current_progress:
            errors.append("No active quiz session found")
            return errors
        
        # Check if already answered in current attempt
        existing_result = QuizResults.query.filter_by(
            user_id=user_id,
            quiz_id=quiz_id,
            question_id=question_id,
            attempt_number=current_progress.attempt_number
        ).first()
        
        if existing_result:
            errors.append("Question already answered in this attempt")
        
        return errors
    
    @staticmethod
    def get_next_question(quiz_id, user_id):
        """Get the next unanswered question for a user in their current attempt"""
        # Get current attempt number
        current_progress = QuizProgress.query.filter_by(
            user_id=user_id,
            quiz_id=quiz_id,
            completed_at=None
        ).first()
        
        if not current_progress:
            return None  # No active session
        
        # Get all questions for this quiz
        all_questions = Questions.query.filter_by(quiz_id=quiz_id).order_by(Questions.id).all()
        
        # Get answered questions for current attempt only
        answered_question_ids = [r.question_id for r in QuizResults.query.filter_by(
            user_id=user_id,
            quiz_id=quiz_id,
            attempt_number=current_progress.attempt_number
        ).all()]
        
        # Find first unanswered question in current attempt
        for question in all_questions:
            if question.id not in answered_question_ids:
                return question
        
        return None  # All questions answered in current attempt
    
    @staticmethod
    def get_quiz_stats(quiz_id, user_id):
        """Calculate quiz statistics for a user's current attempt"""
        # Get current attempt number
        current_progress = QuizProgress.query.filter_by(
            user_id=user_id,
            quiz_id=quiz_id,
            completed_at=None
        ).first()
        
        if current_progress:
            # Get results for current attempt
            results = QuizResults.query.filter_by(
                user_id=user_id,
                quiz_id=quiz_id,
                attempt_number=current_progress.attempt_number
            ).all()
        else:
            # No current attempt, get latest completed attempt results
            latest_attempt = QuizProgress.query.filter_by(
                user_id=user_id,
                quiz_id=quiz_id
            ).order_by(QuizProgress.attempt_number.desc()).first()
            
            if latest_attempt:
                results = QuizResults.query.filter_by(
                    user_id=user_id,
                    quiz_id=quiz_id,
                    attempt_number=latest_attempt.attempt_number
                ).all()
            else:
                results = []
        
        # Get total questions
        total_questions = Questions.query.filter_by(quiz_id=quiz_id).count()
        
        # Calculate stats
        answered_count = len(results)
        correct_count = sum(1 for r in results if r.is_correct)
        
        stats = {
            'total_questions': total_questions,
            'answered_questions': answered_count,
            'correct_answers': correct_count,
            'incorrect_answers': answered_count - correct_count,
            'accuracy': (correct_count / answered_count * 100) if answered_count > 0 else 0,
            'completion': (answered_count / total_questions * 100) if total_questions > 0 else 0,
            'is_completed': answered_count >= total_questions
        }
        
        return stats

def flash_validation_errors(errors):
    """Flash all validation errors"""
    for error in errors:
        flash(error, 'error')

def flash_success_message(message):
    """Flash success message"""
    flash(message, 'success')
