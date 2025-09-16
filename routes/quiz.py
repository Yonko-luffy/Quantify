# routes/quiz.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime
import json
import random

from models import db, Users
from models.quiz import Category, Question, Quiz, QuizAttempt, QuizResult
from utils.validators import QuizValidator, flash_validation_errors

# Create blueprint
quiz_bp = Blueprint('quiz', __name__)


@quiz_bp.route('/')
def index():
    """Landing page with information about the platform"""
    return render_template('index.html')


@quiz_bp.route('/homepage')
@quiz_bp.route('/dashboard')
def homepage():
    """Main quiz dashboard displaying all available quiz templates"""
    quizzes = Quiz.query.filter_by(is_archive=False).order_by(Quiz.created_at.desc()).all()
    users = Users.query.limit(10).all()  # Show recent users for profile viewing
    categories = Category.query.all()  # Get all categories for filter
    
    # Add category information to each quiz
    for quiz in quizzes:
        quiz.category_names = [cat.name for cat in quiz.source_categories]
        # Count available questions in selected categories
        if quiz.source_categories:
            category_ids = [cat.id for cat in quiz.source_categories]
            available_questions = Question.query.filter(Question.category_id.in_(category_ids)).order_by(Question.id).count()
            quiz.has_enough_questions = available_questions >= quiz.number_of_questions
        else:
            quiz.has_enough_questions = False
    
    return render_template('homepage.html', quizzes=quizzes, users=users, categories=categories)


@quiz_bp.route('/quiz/<int:quiz_id>')
@login_required
def quiz_detail(quiz_id):
    """Display quiz template details and start option"""
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Check if quiz has enough questions
    if quiz.source_categories:
        category_ids = [cat.id for cat in quiz.source_categories]
        available_questions = Question.query.filter(Question.category_id.in_(category_ids)).order_by(Question.id).count()
        if available_questions < quiz.number_of_questions:
            flash(f"This quiz requires {quiz.number_of_questions} questions but only {available_questions} are available.", "warning")
            return redirect(url_for('quiz.index'))
    else:
        flash("This quiz has no categories assigned. Please contact an administrator.", "warning")
        return redirect(url_for('quiz.index'))
    
    # Get user's existing attempts
    attempts = QuizAttempt.query.filter_by(
        user_id=current_user.id,
        quiz_id=quiz_id
    ).order_by(QuizAttempt.started_at.desc()).all()
    
    # Check for ongoing attempt
    ongoing_attempt = QuizAttempt.query.filter_by(
        user_id=current_user.id,
        quiz_id=quiz_id,
        completed_at=None
    ).first()
    
    # Get error from URL parameter
    error = request.args.get('error')
    
    # Get questions count for the quiz information display
    questions_count = Question.query.filter_by(category_id=quiz.source_categories[0].id).count() if quiz.source_categories else quiz.number_of_questions
    
    return render_template('quiz.html', 
                         quiz=quiz, 
                         attempts=attempts,
                         ongoing_attempt=ongoing_attempt,
                         questions_count=questions_count,
                         error=error)


@quiz_bp.route('/quiz/<int:quiz_id>/start', methods=['POST'])
@login_required
def start_quiz(quiz_id):
    """Start a new quiz attempt"""
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Check if user has an ongoing attempt
    ongoing_attempt = QuizAttempt.query.filter_by(
        user_id=current_user.id,
        quiz_id=quiz_id,
        completed_at=None
    ).first()
    
    if ongoing_attempt:
        # Resume existing attempt
        return redirect(url_for('quiz.take_quiz', attempt_id=ongoing_attempt.id))
    
    # Verify quiz has enough questions
    if quiz.source_categories:
        category_ids = [cat.id for cat in quiz.source_categories]
        available_questions = Question.query.filter(Question.category_id.in_(category_ids)).order_by(Question.id).all()
        if len(available_questions) < quiz.number_of_questions:
            return redirect(url_for('quiz.quiz_detail', quiz_id=quiz_id, 
                          error="Not enough questions available for this quiz."))
    else:
        return redirect(url_for('quiz.quiz_detail', quiz_id=quiz_id, 
                      error="This quiz has no categories assigned."))
    
    try:
        # Create new quiz attempt
        attempt = QuizAttempt(
            user_id=current_user.id,
            quiz_id=quiz_id,
            started_at=datetime.utcnow()
        )
        db.session.add(attempt)
        db.session.flush()  # Get the attempt ID
        
        # Select first N questions from available pool (simple, consistent approach)
        selected_questions = available_questions[:quiz.number_of_questions]
        
        # Create attempt_questions associations
        for i, question in enumerate(selected_questions):
            attempt.questions.append(question)
        
        db.session.commit()
        
        return redirect(url_for('quiz.take_quiz', attempt_id=attempt.id))
    except Exception as e:
        db.session.rollback()
        return redirect(url_for('quiz.quiz_detail', quiz_id=quiz_id, 
                      error="Failed to start quiz. Please try again."))


@quiz_bp.route('/attempt/<int:attempt_id>/take')
@login_required
def take_quiz(attempt_id):
    """Take a quiz - display current question"""
    attempt = QuizAttempt.query.get_or_404(attempt_id)
    
    # Verify user owns this attempt
    if attempt.user_id != current_user.id:
        flash("You don't have permission to access this quiz attempt.", "error")
        return redirect(url_for('quiz.index'))
    
    # Check if attempt is already completed
    if attempt.completed_at:
        return redirect(url_for('quiz.attempt_results', attempt_id=attempt_id))
    
    # Get error from URL parameter
    error = request.args.get('error')
    
    # Get next unanswered question
    answered_question_ids = [result.question_id for result in attempt.results]
    next_question = None
    
    for question in attempt.questions:
        if question.id not in answered_question_ids:
            next_question = question
            break
    
    # If no more questions, complete the attempt
    if not next_question:
        attempt.completed_at = datetime.utcnow()
        attempt.score = sum(1 for result in attempt.results if result.is_correct)
        db.session.commit()
        return redirect(url_for('quiz.attempt_results', attempt_id=attempt_id))
    
    # Get question position and progress
    question_number = list(attempt.questions).index(next_question) + 1
    total_questions = len(attempt.questions)
    answered_count = len(answered_question_ids)
    
    # Parse question options - handle both JSON strings and lists
    if next_question.options:
        if isinstance(next_question.options, str):
            # Options stored as JSON string
            options_data = json.loads(next_question.options)
        elif isinstance(next_question.options, list):
            # Options already as list
            options_data = next_question.options
        else:
            # Fallback for other types
            options_data = []
    else:
        options_data = []
    
    return render_template('take_quiz.html', 
                         attempt=attempt,
                         quiz=attempt.quiz_template,
                         question=next_question, 
                         options_data=options_data,
                         question_number=question_number,
                         answered_count=answered_count,
                         total_questions=total_questions,
                         error=error)


@quiz_bp.route('/attempt/<int:attempt_id>/submit-answer/<int:question_id>', methods=['POST'])
@login_required
def submit_answer(attempt_id, question_id):
    """Submit an answer for a quiz question"""
    attempt = QuizAttempt.query.get_or_404(attempt_id)
    question = Question.query.get_or_404(question_id)
    
    # Verify user owns this attempt
    if attempt.user_id != current_user.id:
        flash("You don't have permission to access this quiz attempt.", "error")
        return redirect(url_for('quiz.index'))
    
    # Check if attempt is completed
    if attempt.completed_at:
        return redirect(url_for('quiz.attempt_results', attempt_id=attempt_id))
    
    # Check if answer already submitted
    existing_result = QuizResult.query.filter_by(
        attempt_id=attempt_id,
        question_id=question_id
    ).first()
    
    if existing_result:
        return redirect(url_for('quiz.show_feedback', attempt_id=attempt_id, question_id=question_id))
    
    # Get selected answers (support multiple correct answers)
    selected_answers = request.form.getlist('answer', type=int)
    
    if not selected_answers:
        return redirect(url_for('quiz.take_quiz', attempt_id=attempt_id, 
                      error="Please select at least one answer."))
    
    # Validate that question belongs to this attempt
    if question not in attempt.questions:
        return redirect(url_for('quiz.take_quiz', attempt_id=attempt_id, 
                      error="Invalid question for this quiz attempt."))
    
    try:
        # Ensure correct_answers is a list
        if isinstance(question.correct_answers, list):
            correct_answers_list = question.correct_answers
        else:
            # Handle case where correct_answers might be a single value
            correct_answers_list = [question.correct_answers] if question.correct_answers is not None else []
        
        # Check if answer is correct
        is_correct = set(selected_answers) == set(correct_answers_list)
        
        # Save result
        result = QuizResult(
            attempt_id=attempt_id,
            user_id=current_user.id,  # Add user_id field
            question_id=question_id,
            selected_answers=selected_answers,
            is_correct=is_correct,
            answered_at=datetime.utcnow()
        )
        db.session.add(result)
        db.session.commit()
        
        # Redirect to feedback page
        return redirect(url_for('quiz.show_feedback', attempt_id=attempt_id, question_id=question_id))
        
    except Exception as e:
        db.session.rollback()
        # Log the specific error for debugging
        print(f"Error submitting answer: {str(e)}")
        print(f"Selected answers: {selected_answers}")
        print(f"Question correct_answers: {question.correct_answers}")
        print(f"Question correct_answers type: {type(question.correct_answers)}")
        return redirect(url_for('quiz.take_quiz', attempt_id=attempt_id, 
                      error=f"Failed to submit answer: {str(e)}"))


@quiz_bp.route('/attempt/<int:attempt_id>/feedback/<int:question_id>')
@login_required
def show_feedback(attempt_id, question_id):
    """Show feedback for a submitted answer"""
    attempt = QuizAttempt.query.get_or_404(attempt_id)
    question = Question.query.get_or_404(question_id)
    
    # Verify user owns this attempt
    if attempt.user_id != current_user.id:
        flash("You don't have permission to access this quiz attempt.", "error")
        return redirect(url_for('quiz.index'))
    
    # Get user's answer
    result = QuizResult.query.filter_by(
        attempt_id=attempt_id,
        question_id=question_id
    ).first()
    
    if not result:
        return redirect(url_for('quiz.take_quiz', attempt_id=attempt_id, 
                      error="Answer not found."))
    
    # Parse question options - handle both JSON strings and lists
    if question.options:
        if isinstance(question.options, str):
            options_data = json.loads(question.options)
        elif isinstance(question.options, list):
            options_data = question.options
        else:
            options_data = []
    else:
        options_data = []
    
    # Check if this is the last question
    answered_question_ids = [r.question_id for r in attempt.results]
    is_last_question = len(answered_question_ids) >= len(attempt.questions)
    
    # Calculate progress information
    total_questions = len(attempt.questions)
    answered_count = len(answered_question_ids)
    current_question_number = answered_count  # Since we just answered this one
    
    return render_template('answer_feedback.html',
                         attempt=attempt,
                         quiz=attempt.quiz_template,
                         question=question,
                         options_data=options_data,
                         result=result,
                         is_last_question=is_last_question,
                         question_number=current_question_number,
                         total_questions=total_questions,
                         answered_count=answered_count)


@quiz_bp.route('/attempt/<int:attempt_id>/next', methods=['GET', 'POST'])
@login_required
def next_question(attempt_id):
    """Move to the next question after viewing feedback"""
    attempt = QuizAttempt.query.get_or_404(attempt_id)
    
    # Verify user owns this attempt
    if attempt.user_id != current_user.id:
        flash("You don't have permission to access this quiz attempt.", "error")
        return redirect(url_for('quiz.index'))
    
    # Check if all questions are answered
    answered_count = len(attempt.results)
    total_questions = len(attempt.questions)
    
    if answered_count >= total_questions:
        # Complete the attempt
        if not attempt.completed_at:
            attempt.completed_at = datetime.utcnow()
            attempt.score = sum(1 for result in attempt.results if result.is_correct)
            db.session.commit()
        
        return redirect(url_for('quiz.attempt_results', attempt_id=attempt_id))
    
    return redirect(url_for('quiz.take_quiz', attempt_id=attempt_id))


@quiz_bp.route('/attempt/<int:attempt_id>/results')
@login_required
def attempt_results(attempt_id):
    """Display detailed results for a quiz attempt"""
    attempt = QuizAttempt.query.get_or_404(attempt_id)
    
    # Verify user owns this attempt
    if attempt.user_id != current_user.id:
        flash("You don't have permission to access this quiz attempt.", "error")
        return redirect(url_for('quiz.index'))
    
    # Calculate statistics
    total_questions = len(attempt.questions)
    answered_questions = len(attempt.results)
    correct_answers = sum(1 for result in attempt.results if result.is_correct)
    
    stats = {
        'total_questions': total_questions,
        'answered_questions': answered_questions,
        'correct_answers': correct_answers,
        'incorrect_answers': answered_questions - correct_answers,
        'accuracy': (correct_answers / answered_questions * 100) if answered_questions > 0 else 0,
        'completion': (answered_questions / total_questions * 100) if total_questions > 0 else 0,
        'is_completed': attempt.completed_at is not None
    }
    
    # Get detailed results with question data
    detailed_results = []
    for question in attempt.questions:
        result = QuizResult.query.filter_by(
            attempt_id=attempt_id,
            question_id=question.id
        ).first()
        
        if result:
            # Parse question options - handle both JSON strings and lists
            if question.options:
                if isinstance(question.options, str):
                    options_data = json.loads(question.options)
                elif isinstance(question.options, list):
                    options_data = question.options
                else:
                    options_data = []
            else:
                options_data = []
            detailed_results.append({
                'question': question,
                'result': result,
                'options_data': options_data
            })
    
    return render_template('quiz_result.html', 
                         attempt=attempt,
                         quiz=attempt.quiz_template,
                         stats=stats,
                         detailed_results=detailed_results)


@quiz_bp.route('/profile/<username>')
@login_required
def profile(username):
    """Display user profile with quiz history"""
    user = Users.query.filter_by(username=username).first_or_404()
    
    # Get completed quiz attempts
    completed_attempts = QuizAttempt.query.filter_by(
        user_id=user.id
    ).filter(
        QuizAttempt.completed_at.isnot(None)
    ).order_by(QuizAttempt.completed_at.desc()).all()
    
    # Group attempts by quiz
    quiz_history = {}
    for attempt in completed_attempts:
        quiz_id = attempt.quiz_id
        if quiz_id not in quiz_history:
            quiz_history[quiz_id] = {
                'quiz': attempt.quiz_template,
                'attempts': []
            }
        quiz_history[quiz_id]['attempts'].append(attempt)
    
    return render_template('profile.html', user=user, quiz_history=quiz_history)


@quiz_bp.route('/my-quizzes')
@login_required
def my_quizzes():
    """Show current user's quiz attempts and history"""
    # Get ongoing attempts (incomplete)
    ongoing_attempts = QuizAttempt.query.filter_by(
        user_id=current_user.id,
        completed_at=None
    ).order_by(QuizAttempt.started_at.desc()).all()
    
    # Get completed attempts
    completed_attempts = QuizAttempt.query.filter_by(
        user_id=current_user.id
    ).filter(
        QuizAttempt.completed_at.isnot(None)
    ).order_by(QuizAttempt.completed_at.desc()).all()
    
    # Group completed attempts by quiz
    completed_by_quiz = {}
    for attempt in completed_attempts:
        quiz_id = attempt.quiz_id
        if quiz_id not in completed_by_quiz:
            completed_by_quiz[quiz_id] = {
                'quiz': attempt.quiz_template,
                'attempts': []
            }
        completed_by_quiz[quiz_id]['attempts'].append(attempt)
    
    # Calculate statistics
    stats = {
        'total_attempts': len(ongoing_attempts) + len(completed_attempts),
        'in_progress': len(ongoing_attempts),
        'unique_quizzes': len(completed_by_quiz)
    }
    
    # Debug: Check what we're passing to template
    print(f"DEBUG: User {current_user.username} - Total: {stats['total_attempts']}, In Progress: {stats['in_progress']}, Unique: {stats['unique_quizzes']}")
    
    return render_template('my_quizzes.html', 
                         ongoing_attempts=ongoing_attempts,
                         ongoing=ongoing_attempts,  # Keep for backward compatibility
                         completed_by_quiz=completed_by_quiz,
                         stats=stats)


# ================================
# AJAX API Routes
# ================================

@quiz_bp.route('/api/attempt/<int:attempt_id>/progress')
@login_required
def get_attempt_progress(attempt_id):
    """Get progress information for an attempt (AJAX)"""
    attempt = QuizAttempt.query.get_or_404(attempt_id)
    
    # Verify user owns this attempt
    if attempt.user_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403
    
    total_questions = len(attempt.questions)
    answered_questions = len(attempt.results)
    
    return jsonify({
        "total_questions": total_questions,
        "answered_questions": answered_questions,
        "progress_percentage": (answered_questions / total_questions * 100) if total_questions > 0 else 0,
        "is_completed": attempt.completed_at is not None
    })
