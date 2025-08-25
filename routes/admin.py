# routes/admin.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user

from models import db, Users, Quiz, Questions
from utils.decorators import admin_required

# Create blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/')
@admin_required
def admin_panel():
    """Main admin panel dashboard"""
    return render_template('admin_panel.html')


# ================================
# User Management Routes
# ================================

@admin_bp.route('/manage-users')
@admin_required
def manage_users():
    """Display all users for management"""
    users = Users.query.order_by(Users.id.asc()).all()
    error = request.args.get('error')
    return render_template('manage_users.html', users=users, error=error)


@admin_bp.route('/manage-users/<int:user_id>/edit', methods=["POST"])
@admin_required
def edit_user(user_id):
    """Edit user role"""
    new_role = request.form.get("role")
    user = Users.query.get(user_id)

    if user:
        try:
            user.role = new_role
            db.session.commit()
            flash("User role updated successfully.", "success")
            return redirect(url_for("admin.manage_users"))
        except Exception as e:
            db.session.rollback()
            return redirect(url_for("admin.manage_users", error="Failed to update user role."))
    
    return redirect(url_for("admin.manage_users", error="User not found."))


@admin_bp.route('/manage-users/<int:user_id>/delete', methods=["POST"])
@admin_required
def delete_user(user_id):
    """Delete a user"""
    user = Users.query.get(user_id)
    if user:
        # Prevent deleting yourself
        if user.id == current_user.id:
            return redirect(url_for("admin.manage_users", error="You cannot delete your own account."))
        
        try:
            db.session.delete(user)
            db.session.commit()
            flash("User deleted successfully.", "success")
            return redirect(url_for("admin.manage_users"))
        except Exception as e:
            db.session.rollback()
            return redirect(url_for("admin.manage_users", error="Failed to delete user."))
    
    return redirect(url_for("admin.manage_users", error="User not found."))


# ================================
# Quiz Management Routes
# ================================

@admin_bp.route('/quizzes')
@admin_required
def manage_quizzes():
    """Display all quizzes for management"""
    quizzes = Quiz.query.all()
    return render_template('manage_quizzes.html', quizzes=quizzes)


@admin_bp.route('/quizzes/create', methods=["POST"])
@admin_required
def create_quiz():
    """Create a new quiz"""
    quiz_name = request.form.get("quiz_name", "").strip()
    quizzes = Quiz.query.all()  # Get quizzes for error rendering
    
    # Validation - flash error and preserve form data
    if not quiz_name:
        flash("Quiz name is required!", "error")
        return render_template("manage_quizzes.html", quizzes=quizzes, quiz_name=quiz_name)
    
    if len(quiz_name) < 3:
        flash("Quiz name must be at least 3 characters long!", "error")
        return render_template("manage_quizzes.html", quizzes=quizzes, quiz_name=quiz_name)
    
    if Quiz.query.filter_by(name=quiz_name).first():
        flash("A quiz with this name already exists!", "error")
        return render_template("manage_quizzes.html", quizzes=quizzes, quiz_name=quiz_name)
    
    # Success - flash message and redirect (PRG pattern)
    try:
        new_quiz = Quiz(name=quiz_name, created_by=current_user.id)
        db.session.add(new_quiz)
        db.session.commit()
        flash("Quiz created successfully!", "success")
        return redirect(url_for("admin.edit_quiz", quiz_id=new_quiz.id))
    except Exception as e:
        db.session.rollback()
        flash("Quiz creation failed. Please try again!", "error")
        return render_template("manage_quizzes.html", quizzes=quizzes, quiz_name=quiz_name)


@admin_bp.route('/quizzes/<int:quiz_id>/edit', methods=["GET", "POST"])
@admin_required
def edit_quiz(quiz_id):
    """Edit a quiz and its questions"""
    quiz = Quiz.query.get_or_404(quiz_id)
    error = None
    success = None
    
    if request.method == "POST":
        action = request.form.get("action")
        if action == "update_name":
            new_name = request.form.get("quiz_name")
            if new_name and new_name.strip():
                quiz.name = new_name.strip()
                db.session.commit()
                return redirect(url_for("admin.edit_quiz", quiz_id=quiz.id))
        elif action == "add_question":
            question_text = request.form.get("question_text")
            explanation = request.form.get("explanation", "").strip()
            # Normalize whitespace for each option
            options_raw = [request.form.get(f"option{i}") for i in range(1, 6)]
            options = []
            for opt in options_raw:
                if opt:
                    # Remove leading/trailing whitespace and collapse internal spaces
                    normalized = ' '.join(opt.split())
                    if normalized:
                        options.append(normalized)
            answer_index = request.form.get("answer_index")
            
            if question_text and len(options) >= 2 and len(options) <= 5 and answer_index is not None:
                # Check for non-identical options (after normalization)
                if len(set(options)) != len(options):
                    error = "All options must be unique."
                else:
                    try:
                        answer_index = int(answer_index)
                        if answer_index < 0 or answer_index >= len(options):
                            error = "Invalid answer index."
                        else:
                            new_q = Questions(
                                quiz_id=quiz.id, 
                                question_text=question_text, 
                                options=options, 
                                answer_index=answer_index,
                                explanation=explanation if explanation else None
                            )
                            db.session.add(new_q)
                            db.session.commit()
                            return redirect(url_for("admin.edit_quiz", quiz_id=quiz.id))
                    except Exception as e:
                        db.session.rollback()
                        error = "Failed to add question."
            else:
                error = "A question must have 2-5 options and a correct answer."
    
    questions = Questions.query.filter_by(quiz_id=quiz.id).all()
    return render_template("edit_quiz.html", quiz=quiz, questions=questions, error=error, success=success)


@admin_bp.route('/quizzes/<int:quiz_id>/delete', methods=["POST"])
@admin_required
def delete_quiz(quiz_id):
    """Delete a quiz"""
    quiz = Quiz.query.get(quiz_id)
    if quiz:
        db.session.delete(quiz)
        db.session.commit()
        flash("Quiz deleted successfully.", "success")
        return redirect(url_for("admin.manage_quizzes"))
    
    return redirect(url_for("admin.manage_quizzes", error="Quiz not found."))


# ================================
# Question Management Routes
# ================================

@admin_bp.route('/questions/<int:question_id>/edit', methods=["GET", "POST"])
@admin_required
def edit_question(question_id):
    """Edit a single question"""
    question = Questions.query.get_or_404(question_id)
    quiz = Quiz.query.get_or_404(question.quiz_id)
    error = None
    success = None
    
    if request.method == "POST":
        question_text = request.form.get("question_text")
        explanation = request.form.get("explanation", "").strip()
        options = [request.form.get(f"option{i}") for i in range(1, 6) if request.form.get(f"option{i}")]
        answer_index = request.form.get("answer_index")
        
        if question_text and len(options) >= 2 and len(options) <= 5 and answer_index is not None:
            try:
                answer_index = int(answer_index)
                if answer_index < 0 or answer_index >= len(options):
                    error = "Invalid answer index."
                else:
                    question.question_text = question_text
                    question.options = options
                    question.answer_index = answer_index
                    question.explanation = explanation if explanation else None
                    db.session.commit()
                    success = "Question updated."
            except Exception as e:
                db.session.rollback()
                error = "Failed to update question."
        else:
            error = "A question must have 2-5 options and a correct answer."
    
    return render_template("edit_question.html", question=question, quiz=quiz, error=error, success=success)


@admin_bp.route('/questions/<int:question_id>/update-inline', methods=["POST"])
@admin_required
def update_question_inline(question_id):
    """Update a question inline with form submission"""
    question = Questions.query.get_or_404(question_id)
    quiz = Quiz.query.get_or_404(question.quiz_id)
    
    try:
        # Handle form submission
        question_text = request.form.get("question_text", "").strip()
        explanation = request.form.get("explanation", "").strip()
        options = []
        
        # Collect dynamic options from form
        i = 0
        while True:
            option = request.form.get(f"option_{i}", "")
            if option and option.strip():
                options.append(option.strip())
            i += 1
            if i > 10:  # Safety limit
                break
        
        answer_index = request.form.get("answer_index")
        if answer_index is not None:
            try:
                answer_index = int(answer_index)
            except:
                answer_index = None
        
        # Validation with template rendering
        questions = Questions.query.filter_by(quiz_id=quiz.id).all()
        
        if not question_text:
            return render_template("edit_quiz.html", quiz=quiz, questions=questions, error="Question text is required.")
        
        if len(options) < 2:
            return render_template("edit_quiz.html", quiz=quiz, questions=questions, error="At least 2 options are required.")
        
        if len(options) > 5:
            return render_template("edit_quiz.html", quiz=quiz, questions=questions, error="Maximum 5 options allowed.")
        
        # Check for duplicate options
        if len(set(options)) != len(options):
            return render_template("edit_quiz.html", quiz=quiz, questions=questions, error="All options must be unique.")
        
        if answer_index is None or answer_index < 0 or answer_index >= len(options):
            return render_template("edit_quiz.html", quiz=quiz, questions=questions, error="Invalid correct answer selection.")
        
        # Update the question
        question.question_text = question_text
        question.options = options
        question.answer_index = answer_index
        question.explanation = explanation if explanation else None
        db.session.commit()
        
        # Success response with template rendering
        success_msg = "Question updated successfully."
        questions = Questions.query.filter_by(quiz_id=quiz.id).all()
        return render_template("edit_quiz.html", quiz=quiz, questions=questions, success=success_msg)
    
    except Exception as e:
        db.session.rollback()
        error_msg = "Failed to update question."
        questions = Questions.query.filter_by(quiz_id=quiz.id).all()
        return render_template("edit_quiz.html", quiz=quiz, questions=questions, error=error_msg)


@admin_bp.route('/questions/<int:question_id>/delete', methods=["POST"])
@admin_required
def delete_question(question_id):
    """Delete a question"""
    question = Questions.query.get_or_404(question_id)
    quiz_id = question.quiz_id
    db.session.delete(question)
    db.session.commit()
    flash("Question deleted successfully.", "success")
    return redirect(url_for("admin.edit_quiz", quiz_id=quiz_id))
