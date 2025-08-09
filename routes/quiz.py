# routes/quiz.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from models import db, Quiz, Questions, QuizResults, QuizProgress

# Create blueprint
quiz_bp = Blueprint('quiz', __name__)


@quiz_bp.route('/')
@quiz_bp.route('/index')
def index():
    """Main page displaying all available quizzes"""
    quizzes = Quiz.query.all()
    return render_template('index.html', quizzes=quizzes)


@quiz_bp.route('/quiz/<int:quiz_id>')
@login_required  # Optional: remove if you want quizzes public
def quiz_detail(quiz_id):
    """Display a specific quiz"""
    quiz = Quiz.query.get_or_404(quiz_id)
    return render_template('quiz.html', quiz=quiz)


@quiz_bp.route('/quiz/<int:quiz_id>/start', methods=['POST'])
@login_required
def start_quiz(quiz_id):
    """Start a new quiz attempt"""
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Check if user already has progress for this quiz
    existing_progress = QuizProgress.query.filter_by(
        user_id=current_user.id,
        quiz_id=quiz_id,
        completed_at=None
    ).first()
    
    if existing_progress:
        # Resume existing quiz
        return redirect(url_for('quiz.take_quiz', quiz_id=quiz_id))
    
    # Create new progress entry
    progress = QuizProgress(
        user_id=current_user.id,
        quiz_id=quiz_id,
        score=0
    )
    db.session.add(progress)
    db.session.commit()
    
    return redirect(url_for('quiz.take_quiz', quiz_id=quiz_id))


@quiz_bp.route('/quiz/<int:quiz_id>/take')
@login_required
def take_quiz(quiz_id):
    """Take a quiz - display current question"""
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Get user's progress
    progress = QuizProgress.query.filter_by(
        user_id=current_user.id,
        quiz_id=quiz_id,
        completed_at=None
    ).first()
    
    if not progress:
        return redirect(url_for('quiz.quiz_detail', quiz_id=quiz_id))
    
    # Get all questions for this quiz
    questions = Questions.query.filter_by(quiz_id=quiz_id).all()
    
    if not questions:
        flash("This quiz has no questions.", "error")
        return redirect(url_for('quiz.index'))
    
    # Get answered questions
    answered_questions = QuizResults.query.filter_by(
        user_id=current_user.id,
        quiz_id=quiz_id
    ).all()
    
    answered_question_ids = [result.question_id for result in answered_questions]
    
    # Find next unanswered question
    current_question = None
    for question in questions:
        if question.id not in answered_question_ids:
            current_question = question
            break
    
    # If all questions answered, show results
    if not current_question:
        return redirect(url_for('quiz.quiz_results', quiz_id=quiz_id))
    
    return render_template('take_quiz.html', 
                         quiz=quiz, 
                         question=current_question, 
                         progress=progress,
                         answered_count=len(answered_questions),
                         total_questions=len(questions))


@quiz_bp.route('/quiz/<int:quiz_id>/submit_answer/<int:question_id>', methods=['POST'])
@login_required
def submit_answer(quiz_id, question_id):
    """Submit an answer for a quiz question"""
    quiz = Quiz.query.get_or_404(quiz_id)
    question = Questions.query.get_or_404(question_id)
    
    # Verify question belongs to quiz
    if question.quiz_id != quiz_id:
        flash("Invalid question for this quiz.", "error")
        return redirect(url_for('quiz.take_quiz', quiz_id=quiz_id))
    
    # Get user's progress
    progress = QuizProgress.query.filter_by(
        user_id=current_user.id,
        quiz_id=quiz_id,
        completed_at=None
    ).first()
    
    if not progress:
        flash("Quiz session not found.", "error")
        return redirect(url_for('quiz.quiz_detail', quiz_id=quiz_id))
    
    # Check if already answered
    existing_result = QuizResults.query.filter_by(
        user_id=current_user.id,
        quiz_id=quiz_id,
        question_id=question_id
    ).first()
    
    if existing_result:
        flash("Question already answered.", "warning")
        return redirect(url_for('quiz.take_quiz', quiz_id=quiz_id))
    
    # Get selected answer
    selected_index = request.form.get('answer')
    if selected_index is None:
        flash("Please select an answer.", "error")
        return redirect(url_for('quiz.take_quiz', quiz_id=quiz_id))
    
    try:
        selected_index = int(selected_index)
    except ValueError:
        flash("Invalid answer selection.", "error")
        return redirect(url_for('quiz.take_quiz', quiz_id=quiz_id))
    
    # Check if answer is correct
    is_correct = selected_index == question.answer_index
    
    # Save result
    result = QuizResults(
        user_id=current_user.id,
        quiz_id=quiz_id,
        question_id=question_id,
        selected_index=selected_index,
        is_correct=is_correct
    )
    db.session.add(result)
    
    # Update score if correct
    if is_correct:
        progress.score += 1
    
    # Update last question
    progress.last_question_id = question_id
    
    db.session.commit()
    
    return redirect(url_for('quiz.take_quiz', quiz_id=quiz_id))


@quiz_bp.route('/quiz/<int:quiz_id>/results')
@login_required
def quiz_results(quiz_id):
    """Display quiz results"""
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Get user's progress
    progress = QuizProgress.query.filter_by(
        user_id=current_user.id,
        quiz_id=quiz_id
    ).first()
    
    if not progress:
        flash("No quiz attempt found.", "error")
        return redirect(url_for('quiz.quiz_detail', quiz_id=quiz_id))
    
    # Get all results for this quiz attempt
    results = QuizResults.query.filter_by(
        user_id=current_user.id,
        quiz_id=quiz_id
    ).all()
    
    # Get total questions
    total_questions = Questions.query.filter_by(quiz_id=quiz_id).count()
    
    # Mark as completed if not already
    if not progress.completed_at and len(results) == total_questions:
        from datetime import datetime
        progress.completed_at = datetime.utcnow()
        db.session.commit()
    
    return render_template('quiz_result.html', 
                         quiz=quiz, 
                         progress=progress,
                         results=results,
                         total_questions=total_questions)
