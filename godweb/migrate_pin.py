# Migration script to add pin_priority and pinned_by columns to posts table
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from extensions import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    try:
        # Check if columns already exist
        from models import Post

        # Try to add pin_priority column
        try:
            db.session.execute(text('ALTER TABLE posts ADD COLUMN pin_priority INTEGER DEFAULT 0'))
            print("Added pin_priority column")
        except Exception as e:
            print(f"pin_priority column may already exist: {e}")

        # Try to add pinned_by column
        try:
            db.session.execute(text('ALTER TABLE posts ADD COLUMN pinned_by VARCHAR(20)'))
            print("Added pinned_by column")
        except Exception as e:
            print(f"pinned_by column may already exist: {e}")

        db.session.commit()
        print("Migration completed successfully!")

    except Exception as e:
        print(f"Migration error: {e}")
        db.session.rollback()
