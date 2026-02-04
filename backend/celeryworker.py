"""
Celery Worker for Backorder PCM
Runs async tasks for ERP sync, planning, and background jobs
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, create_celery_app

# Create Flask app and Celery app
flask_app = create_app()
celery_app = create_celery_app(flask_app)

if __name__ == '__main__':
    # Run celery worker
    celery_app.start()
