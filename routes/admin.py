# routes/admin.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import current_user
import json

from models import db, Users
from models.quiz import Category, Question, Quiz
from utils.decorators import admin_required

# Create blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/')
@admin_required
def admin_panel():
    """Main admin panel dashboard"""
    # Get some statistics for the dashboard
    total_users = Users.query.count()
    total_categories = Category.query.count()
    total_questions = Question.query.count()
    total_quizzes = Quiz.query.count()
    
    stats = {
        'users': total_users,
        'categories': total_categories,
        'questions': total_questions,
        'quizzes': total_quizzes
    }
    
    return render_template('admin_panel.html', stats=stats)


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
    """Delete a user and all associated data"""
    user = Users.query.get(user_id)
    if user:
        # Prevent deleting yourself
        if user.id == current_user.id:
            return redirect(url_for("admin.manage_users", error="You cannot delete your own account."))
        
        try:
            # Import here to avoid circular imports
            from models.quiz import Quiz, QuizAttempt, QuizResult
            
            # Delete all user's quiz attempts and results first
            QuizAttempt.query.filter_by(user_id=user.id).delete()
            QuizResult.query.filter_by(user_id=user.id).delete()
            
            # Delete quizzes created by this user
            Quiz.query.filter_by(created_by=user.id).delete()
            
            # Finally delete the user
            db.session.delete(user)
            db.session.commit()
            
            flash(f"User '{user.username}' and all associated data deleted successfully.", "success")
            return redirect(url_for("admin.manage_users"))
        except Exception as e:
            db.session.rollback()
            flash(f"Failed to delete user: {str(e)}", "error")
            return redirect(url_for("admin.manage_users"))
    
    flash("User not found.", "error")
    return redirect(url_for("admin.manage_users"))


# ================================
# Category Management Routes
# ================================

@admin_bp.route('/categories')
@admin_required
def manage_categories():
    """Display all categories for management"""
    categories = Category.query.order_by(Category.name.asc()).all()
    # Add question count for each category
    for category in categories:
        category.question_count = Question.query.filter_by(category_id=category.id).count()
    return render_template('manage_categories.html', categories=categories)


@admin_bp.route('/categories/create', methods=["POST"])
@admin_required
def create_category():
    """Create a new category"""
    category_name = request.form.get("category_name", "").strip()
    
    # Validation
    if not category_name:
        flash("Category name is required!", "error")
        return redirect(url_for("admin.manage_categories"))
    
    if len(category_name) < 2:
        flash("Category name must be at least 2 characters long!", "error")
        return redirect(url_for("admin.manage_categories"))
    
    if Category.query.filter_by(name=category_name).first():
        flash("A category with this name already exists!", "error")
        return redirect(url_for("admin.manage_categories"))
    
    try:
        new_category = Category(name=category_name)
        db.session.add(new_category)
        db.session.commit()
        flash("Category created successfully!", "success")
        return redirect(url_for("admin.manage_categories"))
    except Exception as e:
        db.session.rollback()
        flash("Category creation failed. Please try again!", "error")
        return redirect(url_for("admin.manage_categories"))


@admin_bp.route('/categories/<int:category_id>/edit', methods=["POST"])
@admin_required
def edit_category(category_id):
    """Edit a category name"""
    category = Category.query.get_or_404(category_id)
    new_name = request.form.get("category_name", "").strip()
    
    if not new_name:
        flash("Category name is required!", "error")
        return redirect(url_for("admin.manage_categories"))
    
    # Check for duplicate names (excluding current category)
    existing = Category.query.filter(Category.name == new_name, Category.id != category_id).first()
    if existing:
        flash("A category with this name already exists!", "error")
        return redirect(url_for("admin.manage_categories"))
    
    try:
        category.name = new_name
        db.session.commit()
        flash("Category updated successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash("Failed to update category!", "error")
    
    return redirect(url_for("admin.manage_categories"))


@admin_bp.route('/categories/<int:category_id>/delete', methods=["POST"])
@admin_required
def delete_category(category_id):
    """Delete a category"""
    category = Category.query.get_or_404(category_id)
    
    # Check if category has questions
    question_count = Question.query.filter_by(category_id=category_id).count()
    if question_count > 0:
        flash(f"Cannot delete category '{category.name}' - it contains {question_count} questions!", "error")
        return redirect(url_for("admin.manage_categories"))
    
    try:
        db.session.delete(category)
        db.session.commit()
        flash("Category deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash("Failed to delete category!", "error")
    
    return redirect(url_for("admin.manage_categories"))


# ================================
# Question Management Routes  
# ================================

@admin_bp.route('/questions')
@admin_required
def manage_questions():
    """Display all questions for management"""
    category_id = request.args.get('category_id', type=int)
    search = request.args.get('search', '').strip()
    
    # Build query
    query = Question.query
    
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    if search:
        query = query.filter(Question.question_text.contains(search))
    
    questions = query.order_by(Question.id.desc()).all()
    categories = Category.query.order_by(Category.name.asc()).all()
    
    return render_template('manage_questions.html', 
                         questions=questions, 
                         categories=categories,
                         selected_category=category_id,
                         search_term=search)


@admin_bp.route('/questions/create', methods=["GET", "POST"])
@admin_required
def create_question():
    """Create a new question"""
    categories = Category.query.order_by(Category.name.asc()).all()
    
    if request.method == "GET":
        return render_template('create_question.html', categories=categories)
    
    # Handle POST request
    category_id = request.form.get("category_id", type=int)
    question_text = request.form.get("question_text", "").strip()
    explanation = request.form.get("explanation", "").strip()
    
    # Collect options
    options = []
    for i in range(1, 6):  # Support up to 5 options
        option_text = request.form.get(f"option_{i}", "").strip()
        if option_text:
            options.append({"text": option_text, "image_url": None})
    
    # Collect correct answers (multiple choice support)
    correct_answers = []
    for i in range(len(options)):
        if request.form.get(f"correct_{i}"):
            correct_answers.append(i)
    
    # Validation
    errors = []
    if not category_id:
        errors.append("Please select a category.")
    if not question_text:
        errors.append("Question text is required.")
    if len(options) < 2:
        errors.append("At least 2 options are required.")
    if len(options) > 5:
        errors.append("Maximum 5 options allowed.")
    if not correct_answers:
        errors.append("At least one correct answer must be selected.")
    
    # Check for duplicate options
    option_texts = [opt["text"] for opt in options]
    if len(set(option_texts)) != len(option_texts):
        errors.append("All options must be unique.")
    
    if errors:
        for error in errors:
            flash(error, "error")
        return render_template('create_question.html', 
                             categories=categories,
                             form_data=request.form)
    
    try:
        new_question = Question(
            category_id=category_id,
            question_text=question_text,
            options=json.dumps(options),
            correct_answers=correct_answers,
            explanation=explanation if explanation else None
        )
        db.session.add(new_question)
        db.session.commit()
        flash("Question created successfully!", "success")
        return redirect(url_for("admin.manage_questions"))
    except Exception as e:
        db.session.rollback()
        flash("Failed to create question. Please try again!", "error")
        return render_template('create_question.html', 
                             categories=categories,
                             form_data=request.form)


@admin_bp.route('/questions/<int:question_id>/edit', methods=["GET", "POST"])
@admin_required
def edit_question(question_id):
    """Edit an existing question"""
    question = Question.query.get_or_404(question_id)
    categories = Category.query.order_by(Category.name.asc()).all()
    
    if request.method == "GET":
        # Options are already parsed from JSON in the database
        options_data = question.options if question.options else []
        return render_template('edit_question.html', 
                             question=question, 
                             categories=categories,
                             options_data=options_data)
    
    # Handle POST request
    category_id = request.form.get("category_id", type=int)
    question_text = request.form.get("question_text", "").strip()
    explanation = request.form.get("explanation", "").strip()
    
    # Collect options
    options = []
    for i in range(1, 6):  # Support up to 5 options
        option_text = request.form.get(f"option_{i}", "").strip()
        if option_text:
            options.append({"text": option_text, "image_url": None})
    
    # Collect correct answers (multiple choice support)
    correct_answers = []
    for i in range(len(options)):
        if request.form.get(f"correct_{i}"):
            correct_answers.append(i)
    
    # Validation
    errors = []
    if not category_id:
        errors.append("Please select a category.")
    if not question_text:
        errors.append("Question text is required.")
    if len(options) < 2:
        errors.append("At least 2 options are required.")
    if len(options) > 5:
        errors.append("Maximum 5 options allowed.")
    if not correct_answers:
        errors.append("At least one correct answer must be selected.")
    
    # Check for duplicate options
    option_texts = [opt["text"] for opt in options]
    if len(set(option_texts)) != len(option_texts):
        errors.append("All options must be unique.")
    
    if errors:
        for error in errors:
            flash(error, "error")
        options_data = [{"text": opt["text"]} for opt in options]
        return render_template('edit_question.html', 
                             question=question,
                             categories=categories,
                             options_data=options_data,
                             form_data=request.form)
    
    try:
        question.category_id = category_id
        question.question_text = question_text
        question.options = json.dumps(options)
        question.correct_answers = correct_answers
        question.explanation = explanation if explanation else None
        db.session.commit()
        flash("Question updated successfully!", "success")
        return redirect(url_for("admin.manage_questions"))
    except Exception as e:
        db.session.rollback()
        flash("Failed to update question. Please try again!", "error")
        options_data = [{"text": opt["text"]} for opt in options]
        return render_template('edit_question.html', 
                             question=question,
                             categories=categories,
                             options_data=options_data,
                             form_data=request.form)


@admin_bp.route('/questions/<int:question_id>/delete', methods=["POST"])
@admin_required
def delete_question(question_id):
    """Delete a question"""
    question = Question.query.get_or_404(question_id)
    
    try:
        db.session.delete(question)
        db.session.commit()
        flash("Question deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash("Failed to delete question!", "error")
    
    return redirect(url_for("admin.manage_questions"))


@admin_bp.route('/questions/<int:question_id>/quick-edit', methods=["POST"])
@admin_required
def quick_edit_question(question_id):
    """Quick edit question via AJAX"""
    question = Question.query.get_or_404(question_id)
    
    try:
        data = request.get_json()
        
        # Update question text
        if 'question_text' in data:
            question.question_text = data['question_text'].strip()
        
        # Update options
        if 'options' in data:
            # Convert to list of dictionaries
            options = []
            for option_text in data['options']:
                if option_text.strip():
                    options.append({"text": option_text.strip(), "image_url": None})
            question.options = json.dumps(options)
        
        # Update explanation
        if 'explanation' in data:
            explanation = data['explanation'].strip() if data['explanation'] else None
            question.explanation = explanation
        
        db.session.commit()
        return jsonify({"success": True, "message": "Question updated successfully"})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 400


# ================================
# Quiz Template Management Routes
# ================================

@admin_bp.route('/quizzes')
@admin_required
def manage_quizzes():
    """Display all quiz templates for management"""
    quizzes = Quiz.query.order_by(Quiz.created_at.desc()).all()
    # Add category names and question counts
    for quiz in quizzes:
        quiz.category_names = [cat.name for cat in quiz.source_categories]
        # Count available questions in selected categories
        if quiz.source_categories:
            category_ids = [cat.id for cat in quiz.source_categories]
            quiz.available_questions = Question.query.filter(Question.category_id.in_(category_ids)).count()
        else:
            quiz.available_questions = 0
    
    return render_template('manage_quizzes.html', quizzes=quizzes)


@admin_bp.route('/quizzes/create', methods=["GET", "POST"])
@admin_required
def create_quiz():
    """Create a new quiz template"""
    categories = Category.query.order_by(Category.name.asc()).all()
    
    if request.method == "GET":
        return render_template('create_quiz.html', categories=categories)
    
    # Handle POST request
    quiz_name = request.form.get("quiz_name", "").strip()
    description = request.form.get("description", "").strip()
    quiz_type = request.form.get("quiz_type", "standard")
    number_of_questions = request.form.get("number_of_questions", type=int)
    time_limit_minutes = request.form.get("time_limit_minutes", type=int)
    
    # Get selected categories
    selected_category_ids = request.form.getlist("category_ids", type=int)
    
    # Validation
    errors = []
    if not quiz_name:
        errors.append("Quiz name is required.")
    if len(quiz_name) < 3:
        errors.append("Quiz name must be at least 3 characters long.")
    if Quiz.query.filter_by(name=quiz_name).first():
        errors.append("A quiz with this name already exists.")
    if not number_of_questions or number_of_questions < 1:
        errors.append("Number of questions must be at least 1.")
    if number_of_questions and number_of_questions > 50:
        errors.append("Maximum 50 questions allowed per quiz.")
    if not selected_category_ids:
        errors.append("At least one category must be selected.")
    
    # Check if selected categories have enough questions
    if selected_category_ids:
        available_questions = Question.query.filter(Question.category_id.in_(selected_category_ids)).count()
        if number_of_questions and available_questions < number_of_questions:
            errors.append(f"Selected categories only have {available_questions} questions, but you requested {number_of_questions}.")
    
    if errors:
        for error in errors:
            flash(error, "error")
        return render_template('create_quiz.html', 
                             categories=categories,
                             form_data=request.form,
                             selected_categories=selected_category_ids)
    
    try:
        # Create quiz template
        new_quiz = Quiz(
            name=quiz_name,
            description=description,
            quiz_type=quiz_type,
            number_of_questions=number_of_questions,
            time_limit_minutes=time_limit_minutes,
            created_by=current_user.id
        )
        
        # Add selected categories
        selected_categories = Category.query.filter(Category.id.in_(selected_category_ids)).all()
        for category in selected_categories:
            new_quiz.source_categories.append(category)
        
        db.session.add(new_quiz)
        db.session.commit()
        flash("Quiz template created successfully!", "success")
        return redirect(url_for("admin.manage_quizzes"))
    except Exception as e:
        db.session.rollback()
        flash("Failed to create quiz template. Please try again!", "error")
        return render_template('create_quiz.html', 
                             categories=categories,
                             form_data=request.form,
                             selected_categories=selected_category_ids)


@admin_bp.route('/quizzes/<int:quiz_id>/edit', methods=["GET", "POST"])
@admin_required
def edit_quiz(quiz_id):
    """Edit a quiz template"""
    quiz = Quiz.query.get_or_404(quiz_id)
    categories = Category.query.order_by(Category.name.asc()).all()
    
    if request.method == "GET":
        selected_category_ids = [cat.id for cat in quiz.source_categories]
        return render_template('edit_quiz.html', 
                             quiz=quiz, 
                             categories=categories,
                             selected_categories=selected_category_ids)
    
    # Handle POST request
    quiz_name = request.form.get("quiz_name", "").strip()
    description = request.form.get("description", "").strip()
    quiz_type = request.form.get("quiz_type", "standard")
    number_of_questions = request.form.get("number_of_questions", type=int)
    time_limit_minutes = request.form.get("time_limit_minutes", type=int)
    
    # Get selected categories
    selected_category_ids = request.form.getlist("category_ids", type=int)
    
    # Validation
    errors = []
    if not quiz_name:
        errors.append("Quiz name is required.")
    if len(quiz_name) < 3:
        errors.append("Quiz name must be at least 3 characters long.")
    
    # Check for duplicate names (excluding current quiz)
    existing = Quiz.query.filter(Quiz.name == quiz_name, Quiz.id != quiz_id).first()
    if existing:
        errors.append("A quiz with this name already exists.")
    
    if not number_of_questions or number_of_questions < 1:
        errors.append("Number of questions must be at least 1.")
    if number_of_questions and number_of_questions > 50:
        errors.append("Maximum 50 questions allowed per quiz.")
    if not selected_category_ids:
        errors.append("At least one category must be selected.")
    
    # Check if selected categories have enough questions
    if selected_category_ids:
        available_questions = Question.query.filter(Question.category_id.in_(selected_category_ids)).count()
        if number_of_questions and available_questions < number_of_questions:
            errors.append(f"Selected categories only have {available_questions} questions, but you requested {number_of_questions}.")
    
    if errors:
        for error in errors:
            flash(error, "error")
        return render_template('edit_quiz.html', 
                             quiz=quiz,
                             categories=categories,
                             selected_categories=selected_category_ids,
                             form_data=request.form)
    
    try:
        # Update quiz template
        quiz.name = quiz_name
        quiz.description = description
        quiz.quiz_type = quiz_type
        quiz.number_of_questions = number_of_questions
        quiz.time_limit_minutes = time_limit_minutes
        
        # Update categories (clear and re-add)
        quiz.source_categories.clear()
        selected_categories = Category.query.filter(Category.id.in_(selected_category_ids)).all()
        for category in selected_categories:
            quiz.source_categories.append(category)
        
        db.session.commit()
        flash("Quiz template updated successfully!", "success")
        return redirect(url_for("admin.manage_quizzes"))
    except Exception as e:
        db.session.rollback()
        flash("Failed to update quiz template. Please try again!", "error")
        return render_template('edit_quiz.html', 
                             quiz=quiz,
                             categories=categories,
                             selected_categories=selected_category_ids,
                             form_data=request.form)


@admin_bp.route('/quizzes/<int:quiz_id>/delete', methods=["POST"])
@admin_required
def delete_quiz(quiz_id):
    """Delete a quiz template"""
    quiz = Quiz.query.get_or_404(quiz_id)
    
    try:
        db.session.delete(quiz)
        db.session.commit()
        flash("Quiz template deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash("Failed to delete quiz template!", "error")
    
    return redirect(url_for("admin.manage_quizzes"))


# ================================
# AJAX API Routes for Dynamic Content
# ================================

@admin_bp.route('/api/categories/<int:category_id>/questions-count')
@admin_required
def get_category_questions_count(category_id):
    """Get question count for a specific category (AJAX)"""
    count = Question.query.filter_by(category_id=category_id).count()
    return jsonify({"count": count})


@admin_bp.route('/api/categories/questions-count', methods=["POST"])
@admin_required
def get_multiple_categories_questions_count():
    """Get total question count for multiple categories (AJAX)"""
    category_ids = request.json.get("category_ids", [])
    if not category_ids:
        return jsonify({"count": 0})
    
    count = Question.query.filter(Question.category_id.in_(category_ids)).count()
    return jsonify({"count": count})


@admin_bp.route('/question/<int:question_id>/details')
@admin_required
def get_question_details(question_id):
    """Get question details for viewing (AJAX)"""
    question = Question.query.get_or_404(question_id)
    
    return jsonify({
        'id': question.id,
        'question_text': question.question_text,
        'question_type': 'Multiple Choice' if len(question.correct_answers) > 1 else 'Single Choice',
        'options': question.options,
        'correct_option': question.correct_answers,
        'explanation': question.explanation,
        'category': question.category.name
    })
