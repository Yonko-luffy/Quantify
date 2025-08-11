#!/usr/bin/env python3
"""
Add explanation column to questions table using Flask-SQLAlchemy
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db

def add_explanation_column():
    """Add explanation column to questions table"""
    
    try:
        with app.app_context():
            # Check if column already exists by checking table schema
            try:
                result = db.session.execute(db.text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'questions' AND column_name = 'explanation'
                """))
                if result.fetchone():
                    print("Explanation column already exists.")
                    return True
            except Exception as e:
                db.session.rollback()
                print(f"Error checking column: {e}")
            
            # Add the explanation column
            try:
                print("Adding explanation column...")
                db.session.execute(db.text("ALTER TABLE questions ADD COLUMN explanation TEXT"))
                db.session.commit()
                print("Successfully added explanation column to questions table.")
                return True
            except Exception as e:
                db.session.rollback()
                print(f"Error adding column: {e}")
                return False
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    print("Adding explanation column to questions table...")
    success = add_explanation_column()
    
    if success:
        print("Migration completed successfully!")
        sys.exit(0)
    else:
        print("Migration failed!")
        sys.exit(1)
