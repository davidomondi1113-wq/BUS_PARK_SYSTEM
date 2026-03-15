from flask_sqlalchemy import SQLAlchemy

# Shared SQLAlchemy instance across the app
# Initialize with app in main.py

db = SQLAlchemy()
