# utils/validators.py
from flask import flash
import re
from models import Users
from models.quiz import Category, Question, Quiz, QuizAttempt, QuizResult

class QuizValidator:
    """Simplified quiz validation utility for new schema"""
    
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
    def validate_question_data(question_text, options, correct_answers):
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
                if not option or not option.get('text', '').strip():
                    errors.append(f"Option {i+1} cannot be empty")
                elif len(option.get('text', '').strip()) > 255:
                    errors.append(f"Option {i+1} cannot exceed 255 characters")
                else:
                    valid_options.append(option['text'].strip())
            
            # Check for duplicate options
            if len(set(valid_options)) != len(valid_options):
                errors.append("All options must be unique")
        
        # Answer validation
        if not correct_answers:
            errors.append("At least one correct answer must be selected")
        elif any(idx >= len(options) or idx < 0 for idx in correct_answers):
            errors.append("Invalid correct answer selection")
        
        return errors

    @staticmethod
    def validate_category_name(name):
        """Validate category name"""
        errors = []
        
        if not name:
            errors.append("Category name is required")
        elif len(name.strip()) < 2:
            errors.append("Category name must be at least 2 characters long")
        elif len(name.strip()) > 100:
            errors.append("Category name cannot exceed 100 characters")
        elif not re.match(r'^[a-zA-Z0-9\s\-_&.,!?()]+$', name.strip()):
            errors.append("Category name contains invalid characters")
        
        return errors


def flash_validation_errors(errors):
    """Flash multiple validation errors"""
    for error in errors:
        flash(error, 'error')

def flash_success_message(message):
    """Flash success message"""
    flash(message, 'success')
