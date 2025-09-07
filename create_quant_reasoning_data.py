#!/usr/bin/env python3
"""
Script to populate the database with quantitative and reasoning quiz data
Contains 10 quizzes with 10-20 questions each focused on quantitative aptitude and logical reasoning
"""

import sys
sys.path.append('.')

from app import app, db
from models import Category, Question, Quiz, Users
from werkzeug.security import generate_password_hash

def create_quant_reasoning_data(force_recreate=False):
    """Create quantitative and reasoning categories, questions, and quizzes
    
    Args:
        force_recreate (bool): If True, will clear existing data and recreate everything
    """
    
    with app.app_context():
        print("🚀 Checking for sample quantitative and reasoning quiz data...")
        
        # Check if sample quiz data already exists (specific categories that indicate sample data)
        sample_categories = [
            "Numerical Ability", "Logical Reasoning", "Data Interpretation", 
            "Analytical Reasoning", "Mathematical Operations"
        ]
        
        existing_sample_categories = Category.query.filter(
            Category.name.in_(sample_categories)
        ).count()
        
        # Also check for our specific sample quizzes
        sample_quiz_names = [
            "Numerical Aptitude Foundation", "Logical Reasoning Mastery", 
            "Complete Quantitative Aptitude"
        ]
        
        existing_sample_quizzes = Quiz.query.filter(
            Quiz.name.in_(sample_quiz_names)
        ).count()
        
        # Consider sample data exists if we have most sample categories AND sample quizzes
        sample_data_exists = (existing_sample_categories >= 3 and existing_sample_quizzes >= 2)
        
        total_categories = Category.query.count()
        total_questions = Question.query.count()
        total_quizzes = Quiz.query.count()
        
        if sample_data_exists:
            if not force_recreate:
                print(f"✅ Sample quiz data already exists:")
                print(f"   • {existing_sample_categories} sample categories")
                print(f"   • {existing_sample_quizzes} sample quizzes")
                print(f"   • Total: {total_categories} categories, {total_questions} questions, {total_quizzes} quizzes")
                print("   Skipping sample data creation. Use force_recreate=True to override.")
                return
            else:
                print("🔄 Force recreate enabled. Clearing existing data...")
                # Clear existing data in proper order (handle foreign key constraints)
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
                    print("✅ Existing data cleared.")
                except Exception as e:
                    print(f"Error clearing data: {e}")
                    db.session.rollback()
                    return
        
        print("📝 No sample quiz data found. Creating quantitative and reasoning sample content...")
        
        # Create categories for quantitative and reasoning
        categories = [
            Category(name="Numerical Ability"),
            Category(name="Logical Reasoning"), 
            Category(name="Data Interpretation"),
            Category(name="Analytical Reasoning"),
            Category(name="Mathematical Operations"),
            Category(name="Number Series"),
            Category(name="Percentage & Profit Loss"),
            Category(name="Time & Distance"),
            Category(name="Probability & Statistics"),
            Category(name="Pattern Recognition")
        ]
        
        for category in categories:
            db.session.add(category)
        
        db.session.commit()
        print(f"✅ Created {len(categories)} categories")
        
        # Get category objects
        numerical_cat = Category.query.filter_by(name="Numerical Ability").first()
        logical_cat = Category.query.filter_by(name="Logical Reasoning").first()
        data_cat = Category.query.filter_by(name="Data Interpretation").first()
        analytical_cat = Category.query.filter_by(name="Analytical Reasoning").first()
        math_ops_cat = Category.query.filter_by(name="Mathematical Operations").first()
        series_cat = Category.query.filter_by(name="Number Series").first()
        percentage_cat = Category.query.filter_by(name="Percentage & Profit Loss").first()
        time_dist_cat = Category.query.filter_by(name="Time & Distance").first()
        prob_stats_cat = Category.query.filter_by(name="Probability & Statistics").first()
        pattern_cat = Category.query.filter_by(name="Pattern Recognition").first()

        # Create comprehensive question bank
        questions_data = [
            # NUMERICAL ABILITY QUESTIONS
            {
                'category': numerical_cat,
                'text': 'What is 15% of 240?',
                'options': [
                    {'text': '36'},
                    {'text': '38'},
                    {'text': '42'},
                    {'text': '45'}
                ],
                'correct': [0],
                'explanation': '15% of 240 = (15/100) × 240 = 36'
            },
            {
                'category': numerical_cat,
                'text': 'If 3x + 7 = 22, what is the value of x?',
                'options': [
                    {'text': '3'},
                    {'text': '5'},
                    {'text': '7'},
                    {'text': '9'}
                ],
                'correct': [1],
                'explanation': '3x + 7 = 22 → 3x = 15 → x = 5'
            },
            {
                'category': numerical_cat,
                'text': 'What is the square root of 169?',
                'options': [
                    {'text': '11'},
                    {'text': '12'},
                    {'text': '13'},
                    {'text': '14'}
                ],
                'correct': [2],
                'explanation': '√169 = 13 because 13² = 169'
            },
            {
                'category': numerical_cat,
                'text': 'Which of the following are factors of 24?',
                'options': [
                    {'text': '2'},
                    {'text': '3'},
                    {'text': '5'},
                    {'text': '6'},
                    {'text': '8'}
                ],
                'correct': [0, 1, 3, 4],
                'explanation': 'Factors of 24 are: 1, 2, 3, 4, 6, 8, 12, 24. So 2, 3, 6, and 8 are correct.'
            },
            {
                'category': numerical_cat,
                'text': 'What is 2/3 + 1/4?',
                'options': [
                    {'text': '11/12'},
                    {'text': '3/7'},
                    {'text': '5/6'},
                    {'text': '7/8'}
                ],
                'correct': [0],
                'explanation': '2/3 + 1/4 = 8/12 + 3/12 = 11/12'
            },
            
            # LOGICAL REASONING QUESTIONS
            {
                'category': logical_cat,
                'text': 'All roses are flowers. Some flowers are red. Which conclusion is valid?',
                'options': [
                    {'text': 'All roses are red'},
                    {'text': 'Some roses are red'},
                    {'text': 'No roses are red'},
                    {'text': 'Cannot be determined'}
                ],
                'correct': [3],
                'explanation': 'We cannot determine if roses are red from the given statements.'
            },
            {
                'category': logical_cat,
                'text': 'In a code, CHAIR is written as DIBJS. How is TABLE written?',
                'options': [
                    {'text': 'UBCMF'},
                    {'text': 'UCDMF'},
                    {'text': 'TBCMF'},
                    {'text': 'UBDMF'}
                ],
                'correct': [0],
                'explanation': 'Each letter is shifted by +1: C→D, H→I, A→B, I→J, R→S. So T→U, A→B, B→C, L→M, E→F = UBCMF'
            },
            {
                'category': logical_cat,
                'text': 'If Monday is the 1st day, what day is the 15th?',
                'options': [
                    {'text': 'Monday'},
                    {'text': 'Tuesday'},
                    {'text': 'Wednesday'},
                    {'text': 'Thursday'}
                ],
                'correct': [0],
                'explanation': '15 = 2×7 + 1, so 15th day is same as 1st day = Monday'
            },
            {
                'category': logical_cat,
                'text': 'Complete the series: A, C, F, J, ?',
                'options': [
                    {'text': 'O'},
                    {'text': 'P'},
                    {'text': 'Q'},
                    {'text': 'R'}
                ],
                'correct': [0],
                'explanation': 'Differences: +2, +3, +4, so next is +5. J + 5 = O'
            },
            {
                'category': logical_cat,
                'text': 'Which are odd numbers?',
                'options': [
                    {'text': '15'},
                    {'text': '28'},
                    {'text': '37'},
                    {'text': '44'},
                    {'text': '51'}
                ],
                'correct': [0, 2, 4],
                'explanation': 'Odd numbers end in 1, 3, 5, 7, 9. So 15, 37, and 51 are odd.'
            },
            
            # DATA INTERPRETATION QUESTIONS
            {
                'category': data_cat,
                'text': 'A chart shows sales: Jan=100, Feb=150, Mar=120. What is the average monthly sales?',
                'options': [
                    {'text': '120'},
                    {'text': '123.33'},
                    {'text': '125'},
                    {'text': '130'}
                ],
                'correct': [1],
                'explanation': 'Average = (100 + 150 + 120) / 3 = 370 / 3 = 123.33'
            },
            {
                'category': data_cat,
                'text': 'In a pie chart, if one sector is 72°, what percentage does it represent?',
                'options': [
                    {'text': '18%'},
                    {'text': '20%'},
                    {'text': '22%'},
                    {'text': '25%'}
                ],
                'correct': [1],
                'explanation': '72° out of 360° = 72/360 = 1/5 = 20%'
            },
            {
                'category': data_cat,
                'text': 'A table shows: Product A sold 200 units at $10 each, Product B sold 150 units at $15 each. What is total revenue?',
                'options': [
                    {'text': '$4000'},
                    {'text': '$4250'},
                    {'text': '$4500'},
                    {'text': '$4750'}
                ],
                'correct': [1],
                'explanation': 'Revenue = (200 × $10) + (150 × $15) = $2000 + $2250 = $4250'
            },
            {
                'category': data_cat,
                'text': 'Growth from 80 to 120 represents what percentage increase?',
                'options': [
                    {'text': '40%'},
                    {'text': '45%'},
                    {'text': '50%'},
                    {'text': '55%'}
                ],
                'correct': [2],
                'explanation': 'Increase = 40, Percentage = (40/80) × 100 = 50%'
            },
            {
                'category': data_cat,
                'text': 'Which quarters show profit > $50k? Q1=$45k, Q2=$60k, Q3=$55k, Q4=$48k',
                'options': [
                    {'text': 'Q1'},
                    {'text': 'Q2'},
                    {'text': 'Q3'},
                    {'text': 'Q4'}
                ],
                'correct': [1, 2],
                'explanation': 'Q2 ($60k) and Q3 ($55k) both exceed $50k'
            },
            
            # ANALYTICAL REASONING QUESTIONS
            {
                'category': analytical_cat,
                'text': 'Five friends sit in a row. A is not at either end. B is to the right of C. Where could A be?',
                'options': [
                    {'text': 'Position 2'},
                    {'text': 'Position 3'},
                    {'text': 'Position 4'},
                    {'text': 'Cannot be determined'}
                ],
                'correct': [0, 1, 2],
                'explanation': 'A is not at positions 1 or 5, so A can be at positions 2, 3, or 4'
            },
            {
                'category': analytical_cat,
                'text': 'If all Zorks are Blums and some Blums are Groks, which is necessarily true?',
                'options': [
                    {'text': 'All Zorks are Groks'},
                    {'text': 'Some Zorks are Groks'},
                    {'text': 'No Zorks are Groks'},
                    {'text': 'Cannot be determined'}
                ],
                'correct': [3],
                'explanation': 'We cannot determine the relationship between Zorks and Groks from given information'
            },
            {
                'category': analytical_cat,
                'text': 'A cube has 6 faces painted. It is cut into 8 smaller cubes. How many small cubes have exactly 3 painted faces?',
                'options': [
                    {'text': '6'},
                    {'text': '8'},
                    {'text': '12'},
                    {'text': '0'}
                ],
                'correct': [1],
                'explanation': 'Corner cubes have 3 painted faces. A cube cut into 8 parts has 8 corners.'
            },
            {
                'category': analytical_cat,
                'text': 'In a family tree, if A is B\'s father and C is B\'s son, what is A to C?',
                'options': [
                    {'text': 'Father'},
                    {'text': 'Grandfather'},
                    {'text': 'Uncle'},
                    {'text': 'Son'}
                ],
                'correct': [1],
                'explanation': 'A is B\'s father, C is B\'s son, so A is C\'s grandfather'
            },
            {
                'category': analytical_cat,
                'text': 'Which arrangements are possible if Red comes before Blue and Green comes after Blue?',
                'options': [
                    {'text': 'Red, Blue, Green'},
                    {'text': 'Red, Green, Blue'},
                    {'text': 'Blue, Red, Green'},
                    {'text': 'Green, Red, Blue'}
                ],
                'correct': [0],
                'explanation': 'Red before Blue and Green after Blue gives order: Red, Blue, Green'
            },
            
            # MATHEMATICAL OPERATIONS QUESTIONS
            {
                'category': math_ops_cat,
                'text': 'What is 24 ÷ 6 × 3 + 2?',
                'options': [
                    {'text': '14'},
                    {'text': '16'},
                    {'text': '18'},
                    {'text': '20'}
                ],
                'correct': [0],
                'explanation': 'Following BODMAS: 24 ÷ 6 × 3 + 2 = 4 × 3 + 2 = 12 + 2 = 14'
            },
            {
                'category': math_ops_cat,
                'text': 'If a⊕b = a² + b², what is 3⊕4?',
                'options': [
                    {'text': '25'},
                    {'text': '49'},
                    {'text': '7'},
                    {'text': '12'}
                ],
                'correct': [0],
                'explanation': '3⊕4 = 3² + 4² = 9 + 16 = 25'
            },
            {
                'category': math_ops_cat,
                'text': 'What is 2³ + 3² - 4¹?',
                'options': [
                    {'text': '13'},
                    {'text': '15'},
                    {'text': '17'},
                    {'text': '19'}
                ],
                'correct': [0],
                'explanation': '2³ + 3² - 4¹ = 8 + 9 - 4 = 13'
            },
            {
                'category': math_ops_cat,
                'text': 'If x = 5 and y = 3, what is x² - y²?',
                'options': [
                    {'text': '16'},
                    {'text': '18'},
                    {'text': '20'},
                    {'text': '22'}
                ],
                'correct': [0],
                'explanation': 'x² - y² = 5² - 3² = 25 - 9 = 16'
            },
            {
                'category': math_ops_cat,
                'text': 'Which operations give result 12?',
                'options': [
                    {'text': '3 × 4'},
                    {'text': '24 ÷ 2'},
                    {'text': '15 - 3'},
                    {'text': '8 + 4'},
                    {'text': '2⁶ ÷ 16'}
                ],
                'correct': [0, 2, 3],
                'explanation': '3×4=12, 15-3=12, 8+4=12. But 24÷2=12 and 2⁶÷16=64÷16=4'
            },
            
            # NUMBER SERIES QUESTIONS
            {
                'category': series_cat,
                'text': 'What comes next: 2, 6, 18, 54, ?',
                'options': [
                    {'text': '162'},
                    {'text': '108'},
                    {'text': '216'},
                    {'text': '324'}
                ],
                'correct': [0],
                'explanation': 'Each term is multiplied by 3: 2×3=6, 6×3=18, 18×3=54, 54×3=162'
            },
            {
                'category': series_cat,
                'text': 'Find the missing number: 1, 4, 9, 16, ?, 36',
                'options': [
                    {'text': '20'},
                    {'text': '25'},
                    {'text': '30'},
                    {'text': '32'}
                ],
                'correct': [1],
                'explanation': 'Perfect squares: 1², 2², 3², 4², 5², 6² = 1, 4, 9, 16, 25, 36'
            },
            {
                'category': series_cat,
                'text': 'Complete: 3, 7, 15, 31, ?',
                'options': [
                    {'text': '63'},
                    {'text': '62'},
                    {'text': '64'},
                    {'text': '65'}
                ],
                'correct': [0],
                'explanation': 'Each term: previous × 2 + 1. So 31 × 2 + 1 = 63'
            },
            {
                'category': series_cat,
                'text': 'What is the pattern in: 1, 1, 2, 3, 5, 8, ?',
                'options': [
                    {'text': '11'},
                    {'text': '12'},
                    {'text': '13'},
                    {'text': '14'}
                ],
                'correct': [2],
                'explanation': 'Fibonacci series: each term is sum of previous two. 5 + 8 = 13'
            },
            {
                'category': series_cat,
                'text': 'Which numbers follow the pattern 2ⁿ?',
                'options': [
                    {'text': '2'},
                    {'text': '4'},
                    {'text': '6'},
                    {'text': '8'},
                    {'text': '16'}
                ],
                'correct': [0, 1, 3, 4],
                'explanation': '2¹=2, 2²=4, 2³=8, 2⁴=16. But 6 is not a power of 2.'
            },
            
            # PERCENTAGE & PROFIT LOSS QUESTIONS
            {
                'category': percentage_cat,
                'text': 'An item costing $80 is sold for $100. What is the profit percentage?',
                'options': [
                    {'text': '20%'},
                    {'text': '25%'},
                    {'text': '30%'},
                    {'text': '35%'}
                ],
                'correct': [1],
                'explanation': 'Profit = $20, Profit% = (20/80) × 100 = 25%'
            },
            {
                'category': percentage_cat,
                'text': 'If 30% of a number is 60, what is the number?',
                'options': [
                    {'text': '180'},
                    {'text': '200'},
                    {'text': '220'},
                    {'text': '240'}
                ],
                'correct': [1],
                'explanation': '30% of x = 60, so x = 60 ÷ 0.30 = 200'
            },
            {
                'category': percentage_cat,
                'text': 'A shirt marked $50 is sold at 20% discount. What is the selling price?',
                'options': [
                    {'text': '$30'},
                    {'text': '$35'},
                    {'text': '$40'},
                    {'text': '$45'}
                ],
                'correct': [2],
                'explanation': 'Discount = 20% of $50 = $10. Selling price = $50 - $10 = $40'
            },
            {
                'category': percentage_cat,
                'text': 'A population increases from 1000 to 1200. What is the percentage increase?',
                'options': [
                    {'text': '20%'},
                    {'text': '22%'},
                    {'text': '25%'},
                    {'text': '30%'}
                ],
                'correct': [0],
                'explanation': 'Increase = 200, Percentage = (200/1000) × 100 = 20%'
            },
            {
                'category': percentage_cat,
                'text': 'Which represent 50% of their respective totals?',
                'options': [
                    {'text': '25 out of 50'},
                    {'text': '30 out of 60'},
                    {'text': '40 out of 80'},
                    {'text': '35 out of 80'},
                    {'text': '15 out of 30'}
                ],
                'correct': [0, 1, 2, 4],
                'explanation': '50% means half. 25/50, 30/60, 40/80, 15/30 are all half. 35/80 is not.'
            },
            
            # TIME & DISTANCE QUESTIONS
            {
                'category': time_dist_cat,
                'text': 'A car travels 180 km in 3 hours. What is its speed?',
                'options': [
                    {'text': '50 km/h'},
                    {'text': '55 km/h'},
                    {'text': '60 km/h'},
                    {'text': '65 km/h'}
                ],
                'correct': [2],
                'explanation': 'Speed = Distance ÷ Time = 180 ÷ 3 = 60 km/h'
            },
            {
                'category': time_dist_cat,
                'text': 'If a train travels at 80 km/h, how far will it go in 2.5 hours?',
                'options': [
                    {'text': '180 km'},
                    {'text': '200 km'},
                    {'text': '220 km'},
                    {'text': '240 km'}
                ],
                'correct': [1],
                'explanation': 'Distance = Speed × Time = 80 × 2.5 = 200 km'
            },
            {
                'category': time_dist_cat,
                'text': 'Two trains start from opposite ends of a 300 km track. One travels at 70 km/h and other at 80 km/h. When will they meet?',
                'options': [
                    {'text': '1.5 hours'},
                    {'text': '2 hours'},
                    {'text': '2.5 hours'},
                    {'text': '3 hours'}
                ],
                'correct': [1],
                'explanation': 'Combined speed = 70 + 80 = 150 km/h. Time = 300 ÷ 150 = 2 hours'
            },
            {
                'category': time_dist_cat,
                'text': 'A person walks 4 km in 50 minutes. What is his speed in km/h?',
                'options': [
                    {'text': '4.6 km/h'},
                    {'text': '4.8 km/h'},
                    {'text': '5.0 km/h'},
                    {'text': '5.2 km/h'}
                ],
                'correct': [1],
                'explanation': 'Speed = 4 km ÷ (50/60) hours = 4 ÷ 0.833 = 4.8 km/h'
            },
            {
                'category': time_dist_cat,
                'text': 'Which speeds are equivalent to 72 km/h?',
                'options': [
                    {'text': '20 m/s'},
                    {'text': '1200 m/min'},
                    {'text': '72000 m/h'},
                    {'text': '1.2 km/min'}
                ],
                'correct': [0, 1, 2, 3],
                'explanation': '72 km/h = 20 m/s = 1200 m/min = 72000 m/h = 1.2 km/min'
            },
            
            # PROBABILITY & STATISTICS QUESTIONS
            {
                'category': prob_stats_cat,
                'text': 'What is the probability of getting heads in a coin toss?',
                'options': [
                    {'text': '1/4'},
                    {'text': '1/3'},
                    {'text': '1/2'},
                    {'text': '2/3'}
                ],
                'correct': [2],
                'explanation': 'A coin has 2 equally likely outcomes, so P(heads) = 1/2'
            },
            {
                'category': prob_stats_cat,
                'text': 'In rolling a die, what is the probability of getting an even number?',
                'options': [
                    {'text': '1/6'},
                    {'text': '1/3'},
                    {'text': '1/2'},
                    {'text': '2/3'}
                ],
                'correct': [2],
                'explanation': 'Even numbers are 2, 4, 6. So P(even) = 3/6 = 1/2'
            },
            {
                'category': prob_stats_cat,
                'text': 'The mean of 5, 8, 12, 15, 20 is:',
                'options': [
                    {'text': '10'},
                    {'text': '12'},
                    {'text': '14'},
                    {'text': '16'}
                ],
                'correct': [1],
                'explanation': 'Mean = (5 + 8 + 12 + 15 + 20) ÷ 5 = 60 ÷ 5 = 12'
            },
            {
                'category': prob_stats_cat,
                'text': 'What is the median of: 3, 7, 5, 9, 1?',
                'options': [
                    {'text': '3'},
                    {'text': '5'},
                    {'text': '7'},
                    {'text': '9'}
                ],
                'correct': [1],
                'explanation': 'Arranged in order: 1, 3, 5, 7, 9. Middle value (median) = 5'
            },
            {
                'category': prob_stats_cat,
                'text': 'Which represent measures of central tendency?',
                'options': [
                    {'text': 'Mean'},
                    {'text': 'Median'},
                    {'text': 'Mode'},
                    {'text': 'Range'},
                    {'text': 'Standard deviation'}
                ],
                'correct': [0, 1, 2],
                'explanation': 'Mean, median, and mode are measures of central tendency. Range and standard deviation measure spread.'
            },
            
            # PATTERN RECOGNITION QUESTIONS
            {
                'category': pattern_cat,
                'text': 'What comes next in the pattern: △, ○, □, △, ○, ?',
                'options': [
                    {'text': '△'},
                    {'text': '○'},
                    {'text': '□'},
                    {'text': '◊'}
                ],
                'correct': [2],
                'explanation': 'The pattern repeats every 3 shapes: triangle, circle, square'
            },
            {
                'category': pattern_cat,
                'text': 'Complete the pattern: 1A, 3B, 5C, 7D, ?',
                'options': [
                    {'text': '9E'},
                    {'text': '8E'},
                    {'text': '9F'},
                    {'text': '10E'}
                ],
                'correct': [0],
                'explanation': 'Odd numbers with consecutive letters: 1A, 3B, 5C, 7D, 9E'
            },
            {
                'category': pattern_cat,
                'text': 'In the series BAT, CAR, DOG, what comes next?',
                'options': [
                    {'text': 'EGG'},
                    {'text': 'EAR'},
                    {'text': 'ELF'},
                    {'text': 'END'}
                ],
                'correct': [2],
                'explanation': 'Each word starts with the next letter of alphabet: B, C, D, E. ELF follows the pattern.'
            },
            {
                'category': pattern_cat,
                'text': 'What is the next number: 1, 4, 7, 10, ?',
                'options': [
                    {'text': '12'},
                    {'text': '13'},
                    {'text': '14'},
                    {'text': '15'}
                ],
                'correct': [1],
                'explanation': 'Each number increases by 3: 1+3=4, 4+3=7, 7+3=10, 10+3=13'
            },
            {
                'category': pattern_cat,
                'text': 'Which follow the pattern of doubling?',
                'options': [
                    {'text': '2, 4, 8'},
                    {'text': '3, 6, 12'},
                    {'text': '5, 10, 20'},
                    {'text': '4, 8, 12'},
                    {'text': '1, 2, 4'}
                ],
                'correct': [0, 1, 2, 4],
                'explanation': 'Doubling means each term is twice the previous. 4,8,12 does not follow this (12≠8×2).'
            }
        ]
        
        # Create questions
        questions = []
        for q_data in questions_data:
            question = Question(
                category_id=q_data['category'].id,
                question_text=q_data['text'],
                options=q_data['options'],
                correct_answers=q_data['correct'],
                explanation=q_data['explanation']
            )
            db.session.add(question)
            questions.append(question)
        
        db.session.commit()
        print(f"✅ Created {len(questions)} questions with detailed explanations")
        
        # Create admin user if it doesn't exist
        admin = Users.query.filter_by(username='admin').first()
        if not admin:
            # This is the NEW, corrected code
            admin = Users(
                username='admin',
                email='admin@quantify.com',
                password=generate_password_hash('admin123'), 
                role='admin'                                
            )
            db.session.add(admin)
            db.session.commit()
            print("✅ Created admin user (username: admin, password: admin123)")
        
        # Create 10 comprehensive quizzes
        quizzes_data = [
            {
                'name': 'Numerical Aptitude Foundation',
                'description': 'Test your basic numerical calculation and problem-solving skills with fundamental arithmetic operations, percentages, and algebraic concepts.',
                'categories': [numerical_cat, math_ops_cat],
                'time_limit': 25,
                'num_questions': 12
            },
            {
                'name': 'Logical Reasoning Mastery',
                'description': 'Challenge your logical thinking with syllogisms, coding-decoding, series completion, and analytical reasoning problems.',
                'categories': [logical_cat, analytical_cat],
                'time_limit': 30,
                'num_questions': 15
            },
            {
                'name': 'Data Analysis & Interpretation',
                'description': 'Master data interpretation skills with charts, graphs, tables, and statistical analysis questions commonly found in competitive exams.',
                'categories': [data_cat, prob_stats_cat],
                'time_limit': 35,
                'num_questions': 18
            },
            {
                'name': 'Mathematical Operations Challenge',
                'description': 'Test your proficiency in complex mathematical operations, BODMAS rules, algebraic expressions, and numerical computations.',
                'categories': [math_ops_cat, numerical_cat],
                'time_limit': 20,
                'num_questions': 10
            },
            {
                'name': 'Number Series & Patterns',
                'description': 'Develop pattern recognition skills with number series, sequences, and mathematical progressions used in aptitude tests.',
                'categories': [series_cat, pattern_cat],
                'time_limit': 28,
                'num_questions': 14
            },
            {
                'name': 'Profit, Loss & Percentage Mastery',
                'description': 'Master commercial mathematics including profit/loss calculations, percentage problems, discounts, and business arithmetic.',
                'categories': [percentage_cat, numerical_cat],
                'time_limit': 30,
                'num_questions': 16
            },
            {
                'name': 'Time, Speed & Distance',
                'description': 'Solve problems related to time, speed, distance, relative motion, and travel scenarios commonly appearing in quantitative sections.',
                'categories': [time_dist_cat, numerical_cat],
                'time_limit': 25,
                'num_questions': 13
            },
            {
                'name': 'Analytical Reasoning Expert',
                'description': 'Advanced analytical reasoning covering seating arrangements, family relationships, direction sense, and logical deductions.',
                'categories': [analytical_cat, logical_cat],
                'time_limit': 40,
                'num_questions': 20
            },
            {
                'name': 'Probability & Statistics',
                'description': 'Comprehensive coverage of probability theory, statistics, data analysis, central tendencies, and statistical interpretations.',
                'categories': [prob_stats_cat, data_cat],
                'time_limit': 32,
                'num_questions': 17
            },
            {
                'name': 'Complete Quantitative Aptitude',
                'description': 'Ultimate mixed practice test combining all quantitative and reasoning topics for comprehensive skill assessment and exam preparation.',
                'categories': [numerical_cat, logical_cat, data_cat, analytical_cat, math_ops_cat, series_cat, percentage_cat, time_dist_cat, prob_stats_cat, pattern_cat],
                'time_limit': 45,
                'num_questions': 20
            }
        ]
        
        for quiz_data in quizzes_data:
            quiz = Quiz(
                name=quiz_data['name'],
                description=quiz_data['description'],
                time_limit_minutes=quiz_data['time_limit'],
                number_of_questions=quiz_data['num_questions'],
                created_by=admin.id
            )
            db.session.add(quiz)
            db.session.flush()  # Get the quiz ID
            
            # Add source categories to quiz
            for category in quiz_data['categories']:
                quiz.source_categories.append(category)
        
        db.session.commit()
        print(f"✅ Created {len(quizzes_data)} comprehensive quantitative and reasoning quizzes")
        
        print("\n🎉 Quantitative and Reasoning quiz data creation completed successfully!")
        print(f"\n📊 Summary:")
        print(f"   • {len(categories)} specialized categories")
        print(f"   • {len(questions)} high-quality questions with explanations")
        print(f"   • {len(quizzes_data)} comprehensive quizzes (10-20 questions each)")
        print(f"   • Topics covered: Numerical Ability, Logical Reasoning, Data Interpretation,")
        print(f"     Analytical Reasoning, Mathematical Operations, Number Series,")
        print(f"     Percentage & Profit Loss, Time & Distance, Probability & Statistics,")
        print(f"     and Pattern Recognition")
        print("\n🚀 Ready for quantitative aptitude practice!")
        print("\nYou can now:")
        print("1. Login as admin (username: admin, password: admin123)")
        print("2. Take comprehensive quantitative and reasoning quizzes")
        print("3. Practice with detailed explanations for each question")
        print("4. Add more questions through the admin panel")

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Create quantitative and reasoning quiz data')
    parser.add_argument('--force', '-f', action='store_true', 
                        help='Force recreate data even if it already exists')
    
    args = parser.parse_args()
    create_quant_reasoning_data(force_recreate=args.force)
