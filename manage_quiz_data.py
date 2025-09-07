#!/usr/bin/env python3
"""
Quiz Data Management Utility
Provides easy commands to manage quantitative and reasoning quiz data
"""

import sys
import argparse
sys.path.append('.')

from app import app, db
from models import Category, Question, Quiz, QuizAttempt, QuizResult
from create_quant_reasoning_data import create_quant_reasoning_data

def show_status():
    """Show current database status"""
    with app.app_context():
        categories = Category.query.count()
        questions = Question.query.count()
        quizzes = Quiz.query.count()
        attempts = QuizAttempt.query.count()
        
        # Check for sample data specifically
        sample_categories = [
            "Numerical Ability", "Logical Reasoning", "Data Interpretation", 
            "Analytical Reasoning", "Mathematical Operations"
        ]
        
        sample_cats_count = Category.query.filter(
            Category.name.in_(sample_categories)
        ).count()
        
        sample_quiz_names = [
            "Numerical Aptitude Foundation", "Logical Reasoning Mastery", 
            "Complete Quantitative Aptitude"
        ]
        
        sample_quizzes_count = Quiz.query.filter(
            Quiz.name.in_(sample_quiz_names)
        ).count()
        
        print("📊 Current Quiz Database Status:")
        print(f"   • Total Categories: {categories}")
        print(f"   • Total Questions: {questions}")
        print(f"   • Total Quizzes: {quizzes}")
        print(f"   • Quiz Attempts: {attempts}")
        print(f"   • Sample Categories: {sample_cats_count}/{len(sample_categories)}")
        print(f"   • Sample Quizzes: {sample_quizzes_count}/{len(sample_quiz_names)}")
        
        sample_data_complete = (sample_cats_count >= 3 and sample_quizzes_count >= 2)
        print(f"   • Sample Data Status: {'✅ Complete' if sample_data_complete else '❌ Incomplete'}")
        
        if categories > 0:
            print("\n📚 All Categories:")
            for cat in Category.query.all():
                q_count = Question.query.filter_by(category_id=cat.id).count()
                is_sample = cat.name in sample_categories
                marker = "📋" if is_sample else "📄"
                print(f"   {marker} {cat.name}: {q_count} questions")
                
        if quizzes > 0:
            print("\n🎯 All Quizzes:")
            for quiz in Quiz.query.all():
                is_sample = quiz.name in sample_quiz_names
                marker = "🎯" if is_sample else "📝"
                print(f"   {marker} {quiz.name}: {quiz.number_of_questions} questions")

def clear_data():
    """Clear all quiz data (keeping user accounts)"""
    with app.app_context():
        try:
            print("🧹 Clearing quiz data...")
            db.session.query(QuizResult).delete()
            db.session.query(QuizAttempt).delete()
            db.session.execute(db.text("DELETE FROM quiz_source_categories"))
            db.session.execute(db.text("DELETE FROM attempt_questions"))
            db.session.query(Quiz).delete()
            db.session.query(Question).delete()
            db.session.query(Category).delete()
            db.session.commit()
            print("✅ All quiz data cleared successfully")
        except Exception as e:
            print(f"❌ Error clearing data: {e}")
            db.session.rollback()

def create_data():
    """Create fresh quiz data"""
    create_quant_reasoning_data(force_recreate=True)

def reset_data():
    """Reset all quiz data to default"""
    print("🔄 Resetting quiz data to defaults...")
    clear_data()
    create_data()

def main():
    parser = argparse.ArgumentParser(description='Manage Quantify quiz data')
    parser.add_argument('action', choices=['status', 'create', 'clear', 'reset'],
                        help='Action to perform')
    
    args = parser.parse_args()
    
    if args.action == 'status':
        show_status()
    elif args.action == 'create':
        create_data()
    elif args.action == 'clear':
        clear_data()
    elif args.action == 'reset':
        reset_data()

if __name__ == '__main__':
    main()
