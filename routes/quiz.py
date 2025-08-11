# routes/quiz.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
from models import db, Quiz, Questions, QuizResults, QuizProgress, Users
from utils.validators import QuizValidator, flash_validation_errors

# Create blueprint
quiz_bp = Blueprint('quiz', __name__)


@quiz_bp.route('/')
@quiz_bp.route('/index')
def index():
    """Main page displaying all available quizzes"""
    quizzes = Quiz.query.all()
    users = Users.query.limit(10).all()  # Show recent users for profile viewing
    return render_template('index.html', quizzes=quizzes, users=users)


@quiz_bp.route('/quiz/<int:quiz_id>')
@login_required
def quiz_detail(quiz_id):
    """Display quiz details and start option"""
    quiz = Quiz.query.get_or_404(quiz_id)
    questions = Questions.query.filter_by(quiz_id=quiz_id).all()
    
    if not questions:
        flash("This quiz has no questions yet. Please contact an administrator.", "warning")
        return redirect(url_for('quiz.index'))
    
    # Get user's existing progress
    progress = QuizProgress.query.filter_by(
        user_id=current_user.id,
        quiz_id=quiz_id
    ).first()
    
    # Get quiz stats
    stats = QuizValidator.get_quiz_stats(quiz_id, current_user.id)
    
    return render_template('quiz.html', 
                         quiz=quiz, 
                         questions=questions,
                         progress=progress,
                         stats=stats)


@quiz_bp.route('/quiz/<int:quiz_id>/start', methods=['POST'])
@login_required
def start_quiz(quiz_id):
    """Start a new quiz attempt or continue existing one"""
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Check if user has ongoing (incomplete) progress for this quiz
    existing_progress = QuizProgress.query.filter_by(
        user_id=current_user.id,
        quiz_id=quiz_id,
        completed_at=None
    ).first()
    
    if existing_progress:
        # Resume existing incomplete quiz
        return redirect(url_for('quiz.take_quiz', quiz_id=quiz_id))
    
    # Get the next attempt number for this user and quiz
    max_attempt = db.session.query(
        db.func.max(QuizProgress.attempt_number)
    ).filter_by(
        user_id=current_user.id,
        quiz_id=quiz_id
    ).scalar() or 0
    
    next_attempt = max_attempt + 1
    
    # Create new progress entry for new attempt
    progress = QuizProgress(
        user_id=current_user.id,
        quiz_id=quiz_id,
        score=0,
        attempt_number=next_attempt
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
    
    # Get next question using validator
    current_question = QuizValidator.get_next_question(quiz_id, current_user.id)
    
    # If no more questions, show results
    if not current_question:
        # Mark as completed
        progress.completed_at = datetime.utcnow()
        db.session.commit()
        return redirect(url_for('quiz.quiz_results', quiz_id=quiz_id))
    
    # Get question position
    all_questions = Questions.query.filter_by(quiz_id=quiz_id).order_by(Questions.id).all()
    question_number = all_questions.index(current_question) + 1 if current_question in all_questions else 1
    
    # Get answered count for current attempt
    answered_count = QuizResults.query.filter_by(
        user_id=current_user.id,
        quiz_id=quiz_id,
        attempt_number=progress.attempt_number
    ).count()
    
    return render_template('take_quiz.html', 
                         quiz=quiz, 
                         question=current_question, 
                         progress=progress,
                         question_number=question_number,
                         answered_count=answered_count,
                         total_questions=len(all_questions))


@quiz_bp.route('/quiz/<int:quiz_id>/submit_answer/<int:question_id>', methods=['POST'])
@login_required
def submit_answer(quiz_id, question_id):
    """Submit an answer for a quiz question with immediate feedback"""
    selected_index = request.form.get('answer')
    
    # Get current user's active progress
    progress = QuizProgress.query.filter_by(
        user_id=current_user.id,
        quiz_id=quiz_id,
        completed_at=None
    ).first()
    
    if not progress:
        flash("No active quiz session found. Please start the quiz again.", "error")
        return redirect(url_for('quiz.quiz_detail', quiz_id=quiz_id))
    
    # Check if answer already submitted for this attempt
    existing_result = QuizResults.query.filter_by(
        user_id=current_user.id,
        quiz_id=quiz_id,
        question_id=question_id,
        attempt_number=progress.attempt_number
    ).first()
    
    if existing_result:
        # Answer already submitted for this attempt, show feedback
        return redirect(url_for('quiz.show_feedback', quiz_id=quiz_id, question_id=question_id))
    
    # Validate using our validator
    errors = QuizValidator.validate_answer_submission(
        quiz_id, question_id, selected_index, current_user.id
    )
    
    if errors:
        flash_validation_errors(errors)
        return redirect(url_for('quiz.take_quiz', quiz_id=quiz_id))
    
    # Get question
    question = Questions.query.get_or_404(question_id)
    selected_index = int(selected_index)
    is_correct = selected_index == question.answer_index
    
    try:
        # Save result with attempt number
        result = QuizResults(
            user_id=current_user.id,
            quiz_id=quiz_id,
            question_id=question_id,
            selected_index=selected_index,
            is_correct=is_correct,
            attempt_number=progress.attempt_number
        )
        db.session.add(result)
        
        # Update progress
        progress.last_question_id = question_id
        if is_correct:
            progress.score += 1
        
        db.session.commit()
        
        # Redirect to feedback page
        return redirect(url_for('quiz.show_feedback', quiz_id=quiz_id, question_id=question_id))
        
    except Exception as e:
        db.session.rollback()
        flash("Failed to submit answer. Please try again.", "error")
        return redirect(url_for('quiz.take_quiz', quiz_id=quiz_id))


@quiz_bp.route('/quiz/<int:quiz_id>/feedback/<int:question_id>')
@login_required
def show_feedback(quiz_id, question_id):
    """Show feedback for a submitted answer"""
    quiz = Quiz.query.get_or_404(quiz_id)
    question = Questions.query.get_or_404(question_id)
    
    # Get current user's active progress to determine attempt number
    progress = QuizProgress.query.filter_by(
        user_id=current_user.id,
        quiz_id=quiz_id,
        completed_at=None
    ).first()
    
    if not progress:
        flash("No active quiz session found.", "error")
        return redirect(url_for('quiz.quiz_detail', quiz_id=quiz_id))
    
    # Get user's answer for current attempt
    result = QuizResults.query.filter_by(
        user_id=current_user.id,
        quiz_id=quiz_id,
        question_id=question_id,
        attempt_number=progress.attempt_number
    ).first()
    
    if not result:
        flash("Answer not found for current attempt.", "error")
        return redirect(url_for('quiz.take_quiz', quiz_id=quiz_id))
    
    return render_template('answer_feedback.html',
                         quiz=quiz,
                         question=question,
                         selected_index=result.selected_index,
                         is_correct=result.is_correct,
                         correct_answer=question.get_correct_answer(),
                         user_answer=question.options[result.selected_index] if result.selected_index < len(question.options) else None)


@quiz_bp.route('/quiz/<int:quiz_id>/next', methods=['GET', 'POST'])
@login_required
def next_question(quiz_id):
    """Move to the next question after viewing feedback"""
    # Check if quiz is completed
    next_question = QuizValidator.get_next_question(quiz_id, current_user.id)
    
    if not next_question:
        # Quiz completed
        progress = QuizProgress.query.filter_by(
            user_id=current_user.id,
            quiz_id=quiz_id,
            completed_at=None
        ).first()
        
        if progress:
            progress.completed_at = datetime.utcnow()
            db.session.commit()
        
        return redirect(url_for('quiz.quiz_results', quiz_id=quiz_id))
    
    return redirect(url_for('quiz.take_quiz', quiz_id=quiz_id))


@quiz_bp.route('/quiz/<int:quiz_id>/results')
@quiz_bp.route('/quiz/<int:quiz_id>/results/<int:attempt>')
@login_required
def quiz_results(quiz_id, attempt=None):
    """Display detailed quiz results for a specific attempt"""
    quiz = Quiz.query.get_or_404(quiz_id)
    
    if attempt:
        # Get specific attempt progress
        progress = QuizProgress.query.filter_by(
            user_id=current_user.id,
            quiz_id=quiz_id,
            attempt_number=attempt
        ).first()
    else:
        # Get latest attempt progress (completed or current)
        progress = QuizProgress.query.filter_by(
            user_id=current_user.id,
            quiz_id=quiz_id
        ).order_by(QuizProgress.attempt_number.desc()).first()
    
    if not progress:
        flash("No quiz attempt found.", "error")
        return redirect(url_for('quiz.quiz_detail', quiz_id=quiz_id))
    
    # Get detailed results with questions for this specific attempt
    results = db.session.query(QuizResults, Questions).join(
        Questions, QuizResults.question_id == Questions.id
    ).filter(
        QuizResults.user_id == current_user.id,
        QuizResults.quiz_id == quiz_id,
        QuizResults.attempt_number == progress.attempt_number
    ).order_by(Questions.id).all()
    
    # Get quiz statistics for this specific attempt
    if attempt:
        # For specific attempt, calculate stats differently
        total_questions = Questions.query.filter_by(quiz_id=quiz_id).count()
        answered_count = len(results)
        correct_count = sum(1 for result, question in results if result.is_correct)
        
        stats = {
            'total_questions': total_questions,
            'answered_questions': answered_count,
            'correct_answers': correct_count,
            'incorrect_answers': answered_count - correct_count,
            'accuracy': (correct_count / answered_count * 100) if answered_count > 0 else 0,
            'completion': (answered_count / total_questions * 100) if total_questions > 0 else 0,
            'is_completed': answered_count >= total_questions
        }
    else:
        # For current/latest attempt, use validator
        stats = QuizValidator.get_quiz_stats(quiz_id, current_user.id)
    
    return render_template('quiz_result.html', 
                         quiz=quiz, 
                         progress=progress,
                         results=results,
                         stats=stats)


@quiz_bp.route('/profile/<username>')
@login_required
def profile(username):
    """Display user profile with quiz history"""
    user = Users.query.filter_by(username=username).first_or_404()
    
    # Get quiz history with detailed stats
    quiz_history = db.session.query(
        Quiz.id,
        Quiz.name,
        QuizProgress.score,
        QuizProgress.completed_at,
        db.func.count(Questions.id).label('total_questions')
    ).join(
        QuizProgress, Quiz.id == QuizProgress.quiz_id
    ).join(
        Questions, Quiz.id == Questions.quiz_id
    ).filter(
        QuizProgress.user_id == user.id,
        QuizProgress.completed_at.isnot(None)
    ).group_by(
        Quiz.id, Quiz.name, QuizProgress.score, QuizProgress.completed_at
    ).order_by(QuizProgress.completed_at.desc()).all()
    
    return render_template('profile.html', user=user, quiz_history=quiz_history)


@quiz_bp.route('/my-quizzes')
@login_required
def my_quizzes():
    """Show current user's quiz attempts and history with all attempts"""
    # Get ongoing quizzes (incomplete attempts)
    ongoing = db.session.query(Quiz, QuizProgress).join(
        QuizProgress, Quiz.id == QuizProgress.quiz_id
    ).filter(
        QuizProgress.user_id == current_user.id,
        QuizProgress.completed_at.is_(None)
    ).all()
    
    # Get completed quizzes with all attempts grouped by quiz
    completed_raw = db.session.query(
        Quiz.id,
        Quiz.name,
        QuizProgress.score,
        QuizProgress.attempt_number,
        QuizProgress.completed_at,
        db.func.count(Questions.id).label('total_questions')
    ).join(
        QuizProgress, Quiz.id == QuizProgress.quiz_id
    ).join(
        Questions, Quiz.id == Questions.quiz_id
    ).filter(
        QuizProgress.user_id == current_user.id,
        QuizProgress.completed_at.isnot(None)
    ).group_by(
        Quiz.id, Quiz.name, QuizProgress.score, QuizProgress.attempt_number, QuizProgress.completed_at
    ).order_by(Quiz.name, QuizProgress.attempt_number.desc()).all()
    
    # Group completed attempts by quiz
    completed_by_quiz = {}
    for attempt in completed_raw:
        quiz_id = attempt.id
        if quiz_id not in completed_by_quiz:
            completed_by_quiz[quiz_id] = {
                'quiz_name': attempt.name,
                'attempts': []
            }
        completed_by_quiz[quiz_id]['attempts'].append({
            'id': quiz_id,
            'name': attempt.name,
            'score': attempt.score,
            'attempt_number': attempt.attempt_number,
            'completed_at': attempt.completed_at,
            'total_questions': attempt.total_questions
        })
    
    return render_template('my_quizzes.html', 
                         ongoing=ongoing, 
                         completed_by_quiz=completed_by_quiz)
