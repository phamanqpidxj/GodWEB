# Migration script to add missing schema columns used by current app features
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from godweb.extensions import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    try:
        # Check if columns already exist
        from godweb.models import Post

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

        # Try to add product inventory_type column
        try:
            db.session.execute(text("ALTER TABLE products ADD COLUMN inventory_type VARCHAR(20) DEFAULT 'file'"))
            print("Added inventory_type column")
        except Exception as e:
            print(f"inventory_type column may already exist: {e}")

        # Try to add product inventory_folder_path column
        try:
            db.session.execute(text('ALTER TABLE products ADD COLUMN inventory_folder_path VARCHAR(255)'))
            print("Added inventory_folder_path column")
        except Exception as e:
            print(f"inventory_folder_path column may already exist: {e}")

        # Backfill inventory_type for old products
        db.session.execute(text("UPDATE products SET inventory_type = 'file' WHERE inventory_type IS NULL"))

        db.session.commit()
        print("Migration completed successfully!")

    except Exception as e:
        print(f"Migration error: {e}")
        db.session.rollback()
