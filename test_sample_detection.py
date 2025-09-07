#!/usr/bin/env python3
"""
Test script to demonstrate sample quiz detection behavior
"""

import sys
sys.path.append('.')

from app import app, db
from models import Category, Question, Quiz, Users
from werkzeug.security import generate_password_hash

def create_custom_quiz_scenario():
    """Create a scenario with custom quizzes but no sample quizzes"""
    
    with app.app_context():
        print("🧪 Creating test scenario: Custom quizzes without sample quizzes")
        
        # Clear all data first
        from models import QuizAttempt, QuizResult
        try:
            db.session.query(QuizResult).delete()
            db.session.query(QuizAttempt).delete()
            db.session.execute(db.text("DELETE FROM quiz_source_categories"))
            db.session.execute(db.text("DELETE FROM attempt_questions"))
            db.session.query(Quiz).delete()
            db.session.query(Question).delete() 
            db.session.query(Category).delete()
            db.session.commit()
            print("✅ Cleared existing data")
        except Exception as e:
            print(f"Error: {e}")
            db.session.rollback()
            return
        
        # Create custom categories (not sample ones)
        custom_categories = [
            Category(name="Custom Math"),
            Category(name="Custom Science"),
            Category(name="Custom History")
        ]
        
        for category in custom_categories:
            db.session.add(category)
        
        db.session.commit()
        print(f"✅ Created {len(custom_categories)} custom categories")
        
        # Create some custom questions
        math_cat = Category.query.filter_by(name="Custom Math").first()
        
        custom_questions = [
            Question(
                category_id=math_cat.id,
                question_text="What is 2 + 2?",
                options=[
                    {'text': '3'},
                    {'text': '4'},
                    {'text': '5'},
                    {'text': '6'}
                ],
                correct_answers=[1],
                explanation="2 + 2 = 4"
            ),
            Question(
                category_id=math_cat.id,
                question_text="What is 5 x 3?",
                options=[
                    {'text': '15'},
                    {'text': '8'},
                    {'text': '12'},
                    {'text': '20'}
                ],
                correct_answers=[0],
                explanation="5 × 3 = 15"
            )
        ]
        
        for question in custom_questions:
            db.session.add(question)
        
        db.session.commit()
        print(f"✅ Created {len(custom_questions)} custom questions")
        
        # Create admin user
        admin = Users.query.filter_by(username='admin').first()
        if not admin:
            admin = Users(
                username='admin',
                email='admin@quantify.com',
                password_hash=generate_password_hash('admin123'),
                is_admin=True,
                is_verified=True
            )
            db.session.add(admin)
            db.session.commit()
        
        # Create custom quiz (not a sample quiz)
        custom_quiz = Quiz(
            name="Custom Basic Math Quiz",
            description="A custom quiz created by user",
            time_limit_minutes=10,
            number_of_questions=2,
            created_by=admin.id
        )
        
        db.session.add(custom_quiz)
        db.session.flush()
        custom_quiz.source_categories.append(math_cat)
        db.session.commit()
        
        print("✅ Created 1 custom quiz")
        print("\n📊 Test Scenario Created:")
        print("   • 3 custom categories (no sample categories)")
        print("   • 2 custom questions")
        print("   • 1 custom quiz (no sample quizzes)")
        print("   • This should trigger sample quiz creation when app starts!")

if __name__ == '__main__':
    create_custom_quiz_scenario()
